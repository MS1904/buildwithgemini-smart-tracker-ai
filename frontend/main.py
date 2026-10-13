"""FastAPI proxy for deployed A2A agent on Agent Runtime with clean artifact and message parsing."""

import os
import json
import httpx
import google.auth
from google.auth.transport.requests import Request as GoogleAuthRequest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

RESOURCE = os.environ.get(
    "AGENT_ENGINE_RESOURCE_NAME",
    "projects/88951093419/locations/us-central1/reasoningEngines/3663898474069360640",
)
AGENT_DIRECTORY = os.environ.get("AGENT_DIRECTORY", "app")
LOCATION = RESOURCE.split("/locations/")[1].split("/")[0]

A2A_ENDPOINT = (
    f"https://{LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/"
    f"{RESOURCE}/api/a2a/{AGENT_DIRECTORY}"
)

app = FastAPI()

_creds = None

def get_auth_token():
    global _creds
    if _creds is None:
        _creds, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
    if not _creds.valid:
        _creds.refresh(GoogleAuthRequest())
    return _creds.token


@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_msg = body.get("message", "").strip()
    image_data = body.get("image")  # base64 data url
    if not user_msg and not image_data:
        return JSONResponse({"parts": [{"kind": "text", "text": "Empty message."}]})

    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    parts_payload = []
    if user_msg:
        parts_payload.append({"kind": "text", "text": user_msg})

    if image_data:
        # If user uploaded a meal or report image, append vision metadata note
        # A2A accepts data or text parts; describe attachment for agent tools
        parts_payload.append({
            "kind": "text",
            "text": f"\n[User Attached Image: Multimodal input provided via camera/upload. Proceed with visual analysis.]"
        })

    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "messageId": f"msg-{os.urandom(4).hex()}",
                "role": "user",
                "parts": parts_payload,
            }
        },
        "id": 1,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(A2A_ENDPOINT, headers=headers, json=payload)
            if resp.status_code != 200:
                return JSONResponse(
                    {"parts": [{"kind": "text", "text": f"Error from agent runtime (HTTP {resp.status_code}): {resp.text}"}]},
                    status_code=resp.status_code,
                )

            data = resp.json()
            result = data.get("result", {})
            parts = []

            # 1. Check for artifacts with response parts
            artifacts = result.get("artifacts", [])
            for art in artifacts:
                for p in art.get("parts", []):
                    if p.get("kind") == "text" or "text" in p:
                        parts.append({"kind": "text", "text": p.get("text", "")})
                    elif p.get("kind") == "data" or "data" in p:
                        parts.append({"kind": "a2ui", "data": p.get("data", {})})

            # 2. Check for latest agent message in history if no artifact parts found
            if not parts and "history" in result:
                for item in reversed(result["history"]):
                    if item.get("role") == "agent":
                        for p in item.get("parts", []):
                            if p.get("kind") == "text" or "text" in p:
                                parts.append({"kind": "text", "text": p.get("text", "")})
                            elif p.get("kind") == "data" and "response" not in p.get("data", {}):
                                parts.append({"kind": "a2ui", "data": p.get("data", {})})
                        if parts:
                            break

            # 3. Check direct parts
            if not parts and "parts" in result:
                for p in result["parts"]:
                    if p.get("kind") == "text" or "text" in p:
                        parts.append({"kind": "text", "text": p.get("text", "")})
                    elif p.get("kind") == "data":
                        parts.append({"kind": "a2ui", "data": p.get("data", {})})

            if not parts:
                parts.append({"kind": "text", "text": "(The agent completed the request.)"})

            return JSONResponse({"parts": parts})
        except Exception as e:
            return JSONResponse(
                {"parts": [{"kind": "text", "text": f"Proxy request failed: {str(e)}"}]},
                status_code=500,
            )


app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
