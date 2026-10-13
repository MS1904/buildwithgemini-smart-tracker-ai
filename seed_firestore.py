#!/usr/bin/env python3
import datetime
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-f4cdb9206689"

def seed():
    print(f"Connecting to Firestore in project: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)
    
    memories_ref = db.collection("memories")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    sample_memories = [
        {
            "id": "mem_01",
            "category": "preference",
            "key": "peak_focus_window",
            "content": "Prefers deep technical and architectural work in early morning blocks (8:00 AM - 11:00 AM).",
            "confidence": 0.95,
            "tags": ["focus", "morning", "deep work", "schedule"],
            "enabled": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "mem_02",
            "category": "routine",
            "key": "daily_exercise_preference",
            "content": "Prefers physical recovery exercise in the mid-to-late afternoon after high cognitive sessions.",
            "confidence": 0.9,
            "tags": ["exercise", "afternoon", "health", "cardio"],
            "enabled": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "mem_03",
            "category": "goal_context",
            "key": "demo_focus_objective",
            "content": "Primary conference goal is showing offline local-first privacy with Gemini 3.8 Flash evidence reasoning.",
            "confidence": 1.0,
            "tags": ["presentation", "demo", "gemini", "privacy"],
            "enabled": True,
            "created_at": now,
            "updated_at": now,
        },
    ]

    for item in sample_memories:
        doc_ref = memories_ref.document(item["key"])
        doc_ref.set(item)
        print(f"✓ Seeded memory: {item['key']} ({item['category']})")

    print("\nVerifying seeded items from Firestore:")
    for doc in memories_ref.stream():
        d = doc.to_dict()
        print(f" - [{d.get('category')}] {d.get('key')}: {d.get('content')}")

if __name__ == "__main__":
    seed()
