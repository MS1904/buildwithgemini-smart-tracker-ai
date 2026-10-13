# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from typing import Optional, List, Dict, Any
from zoneinfo import ZoneInfo
from google.cloud import firestore

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from .a2ui_utils import a2ui_callback

MODEL = "gemini-3.8-flash"

# Hardcoded GCP Project ID string to prevent Agent Platform project number issue
PROJECT_ID = "qwiklabs-gcp-04-f4cdb9206689"


def _get_firestore_client() -> firestore.Client:
    """Returns a Firestore client bound to the hardcoded project ID."""
    return firestore.Client(project=PROJECT_ID)


def list_memories(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """List stored persistent AI memories from Firestore.

    Args:
        category: Optional category filter ('preference', 'routine', 'goal_context', 'working_context').

    Returns:
        A list of persistent memory dictionaries with keys, categories, contents, and timestamps.
    """
    db = _get_firestore_client()
    memories_ref = db.collection("memories")
    query = memories_ref.where(filter=firestore.FieldFilter("enabled", "==", True))
    if category:
        query = query.where(filter=firestore.FieldFilter("category", "==", category))

    results = []
    for doc in query.stream():
        d = doc.to_dict()
        results.append({
            "key": d.get("key"),
            "category": d.get("category"),
            "content": d.get("content"),
            "tags": d.get("tags", []),
            "confidence": d.get("confidence", 1.0),
            "updated_at": d.get("updated_at"),
        })
    return results


def get_memory(key: str) -> Dict[str, Any]:
    """Retrieve a specific persistent memory by its unique key.

    Args:
        key: The unique string identifier for the memory (e.g. 'peak_focus_window').

    Returns:
        The memory document dict, or an error status if not found.
    """
    db = _get_firestore_client()
    doc_ref = db.collection("memories").document(key)
    doc = doc_ref.get()
    if not doc.exists:
        return {"found": False, "message": f"No memory found with key '{key}'"}
    data = doc.to_dict()
    data["found"] = True
    return data


def save_memory(
    key: str,
    category: str,
    content: str,
    tags: Optional[List[str]] = None,
    confidence: float = 1.0,
) -> Dict[str, Any]:
    """Save or update a persistent memory in Firestore.

    Args:
        key: Unique identifier for the memory (e.g. 'morning_study_time').
        category: One of 'preference', 'routine', 'goal_context', 'working_context'.
        content: The factual statement or preference to remember.
        tags: Optional list of keyword tags for search and relevance.
        confidence: Confidence score between 0.0 and 1.0.

    Returns:
        Confirmation status of the memory save operation.
    """
    db = _get_firestore_client()
    doc_ref = db.collection("memories").document(key)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    existing = doc_ref.get()

    if existing.exists:
        existing_data = existing.to_dict()
        existing_tags = existing_data.get("tags", [])
        combined_tags = list(set((tags or []) + existing_tags))
        doc_ref.update({
            "category": category,
            "content": content,
            "tags": combined_tags,
            "confidence": confidence,
            "updated_at": now,
        })
        return {
            "status": "updated",
            "key": key,
            "message": f"Updated existing memory '{key}'."
        }
    else:
        new_record = {
            "id": f"mem_{key}",
            "key": key,
            "category": category,
            "content": content,
            "tags": tags or [],
            "confidence": confidence,
            "enabled": True,
            "created_at": now,
            "updated_at": now,
        }
        doc_ref.set(new_record)
        return {
            "status": "created",
            "key": key,
            "message": f"Created new memory '{key}'."
        }


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


instruction = (
    "You are Smart Tracker AI's Agent Assistant. You help users manage tasks, routines, and preferences. "
    "You have access to a persistent Firestore memory database where user-approved preferences, routines, "
    "and goal context are stored. Use the list_memories, get_memory, and save_memory tools to inspect, "
    "retrieve, and remember relevant user context when answering.\n\n"
    "When answering, you may return structured A2UI v0.8 JSON cards, or clear formatted markdown summaries."
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[list_memories, get_memory, save_memory, get_weather, get_current_time],
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
