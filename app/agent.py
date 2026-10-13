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


# ============================================================================
# PERSONAL PRODUCTIVITY TOOLS
# ============================================================================

def list_tasks(completed: Optional[bool] = None, priority: Optional[str] = None) -> List[Dict[str, Any]]:
    """List tasks from the user's personal task manager in Firestore.

    Args:
        completed: Optional filter for completion status (True or False). None returns all.
        priority: Optional filter by priority ('high', 'medium', 'low').

    Returns:
        List of tasks with title, priority, due date, estimated minutes, and status.
    """
    db = _get_firestore_client()
    query = db.collection("tasks")
    if completed is not None:
        query = query.where(filter=firestore.FieldFilter("completed", "==", completed))
    if priority:
        query = query.where(filter=firestore.FieldFilter("priority", "==", priority.lower()))

    tasks = []
    for doc in query.stream():
        d = doc.to_dict()
        tasks.append({
            "id": doc.id,
            "title": d.get("title"),
            "category": d.get("category", "general"),
            "priority": d.get("priority", "medium"),
            "estimated_minutes": d.get("estimated_minutes", 30),
            "due_date": d.get("due_date"),
            "completed": d.get("completed", False),
        })
    return tasks


def add_task(title: str, priority: str = "medium", estimated_minutes: int = 30, due_date: Optional[str] = None, category: str = "general") -> Dict[str, Any]:
    """Add a new task to the user's personal productivity tracker.

    Args:
        title: Title/description of the task to be done.
        priority: Task priority level ('high', 'medium', 'low').
        estimated_minutes: Estimated time in minutes required for this task.
        due_date: Due date formatted as YYYY-MM-DD (defaults to today if omitted).
        category: Task category ('work', 'learning', 'health', 'finance', etc.).

    Returns:
        Confirmation dictionary with the newly generated task ID and details.
    """
    db = _get_firestore_client()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    task_id = f"task_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}"
    task_record = {
        "id": task_id,
        "title": title,
        "category": category,
        "priority": priority.lower(),
        "estimated_minutes": estimated_minutes,
        "due_date": due_date or today_str,
        "completed": False,
        "created_at": now,
        "updated_at": now,
    }
    db.collection("tasks").document(task_id).set(task_record)
    return {
        "status": "created",
        "task_id": task_id,
        "title": title,
        "message": f"Successfully created task '{title}' ({priority} priority, {estimated_minutes} min)."
    }


def complete_task(task_id: str) -> Dict[str, Any]:
    """Mark a task as completed in the user's productivity tracker.

    Args:
        task_id: Unique identifier of the task (e.g. 'task_1').

    Returns:
        Status dictionary confirming completion.
    """
    db = _get_firestore_client()
    doc_ref = db.collection("tasks").document(task_id)
    doc = doc_ref.get()
    if not doc.exists:
        return {"status": "not_found", "message": f"Task '{task_id}' not found."}

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    doc_ref.update({"completed": True, "updated_at": now})
    return {"status": "completed", "task_id": task_id, "message": f"Task '{task_id}' marked as completed."}


# ============================================================================
# PERSONAL FINANCE TOOLS
# ============================================================================

def log_expense(amount: float, category: str, description: str, date: Optional[str] = None) -> Dict[str, Any]:
    """Log an expense into the user's personal finance tracker in Firestore.

    Args:
        amount: Dollar amount of the transaction (e.g. 14.50).
        category: Expense category ('food', 'transport', 'learning', 'housing', 'entertainment', etc.).
        description: Merchant or short explanation of the purchase.
        date: Transaction date formatted as YYYY-MM-DD (defaults to today if omitted).

    Returns:
        Confirmation dictionary with the recorded expense ID.
    """
    db = _get_firestore_client()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    exp_id = f"exp_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}"
    exp_record = {
        "id": exp_id,
        "amount": round(float(amount), 2),
        "category": category.lower(),
        "description": description,
        "date": date or today_str,
        "created_at": now,
    }
    db.collection("finances").document(exp_id).set(exp_record)
    return {
        "status": "logged",
        "expense_id": exp_id,
        "amount": exp_record["amount"],
        "category": exp_record["category"],
        "description": description,
        "message": f"Recorded expense of ${exp_record['amount']} for '{description}' under '{exp_record['category']}'."
    }


def get_financial_summary(month: Optional[str] = None) -> Dict[str, Any]:
    """Calculate an aggregated financial breakdown of expenses by category and total spend.

    Args:
        month: Optional month filter string 'YYYY-MM' (e.g. '2026-10'). Defaults to current month.

    Returns:
        Dictionary with total spend, category-by-category breakdown, transaction count, and recent items.
    """
    db = _get_firestore_client()
    today = datetime.datetime.now(datetime.timezone.utc)
    target_prefix = month or today.strftime("%Y-%m")

    query = db.collection("finances").stream()
    total_spent = 0.0
    category_totals: Dict[str, float] = {}
    items = []

    for doc in query:
        d = doc.to_dict()
        doc_date = d.get("date", "")
        if doc_date.startswith(target_prefix):
            amt = float(d.get("amount", 0.0))
            cat = d.get("category", "uncategorized")
            total_spent += amt
            category_totals[cat] = category_totals.get(cat, 0.0) + amt
            items.append({
                "id": doc.id,
                "amount": amt,
                "category": cat,
                "description": d.get("description", ""),
                "date": doc_date,
            })

    # Round totals
    total_spent = round(total_spent, 2)
    breakdown = {k: round(v, 2) for k, v in category_totals.items()}

    return {
        "month": target_prefix,
        "total_spent": total_spent,
        "transaction_count": len(items),
        "category_breakdown": breakdown,
        "recent_expenses": items[-5:],
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
    "You are Smart Tracker AI's Agent Assistant. You help users manage their personal productivity, "
    "habits, routines, personal finances, and long-term memory with evidence-based reasoning.\n\n"
    "Available capabilities:\n"
    "1. Productivity Management: Use 'list_tasks', 'add_task', and 'complete_task' to inspect pending "
    "items, add tasks with estimated minutes and priority, and mark items done.\n"
    "2. Personal Finance: Use 'log_expense' and 'get_financial_summary' to record spending and deliver "
    "clear budget breakdowns by category.\n"
    "3. Persistent Memory: Use 'list_memories', 'get_memory', and 'save_memory' to read and maintain "
    "user-approved preferences (e.g. peak focus window, workout routines).\n"
    "4. Scheduling & Context: Correlate tasks with peak focus windows, check time with 'get_current_time', "
    "and check outdoor conditions with 'get_weather'.\n\n"
    "CRITICAL FORMATTING & PRESENTATION GUIDELINES:\n"
    "- Never output dry, naive, raw JSON or plain wall of text.\n"
    "- Make responses visually captivating, human-readable, warm, and structured.\n"
    "- Use clean Markdown headers (##, ###), bulleted lists, bold highlights, and clean comparison tables.\n"
    "- Use tasteful emojis and status badges (e.g., 🔴 High, 🟡 Medium, 🟢 Low, ✅ Done, ⏱️ Estimated, 💰 Spend, 🧠 Memory, 🎯 Goal).\n"
    "- When presenting tasks or schedules, include estimated completion timelines, priority badges, and practical tips.\n"
    "- When presenting finances, format monetary figures cleanly with category badges, dollar totals, percentage breakdowns, and visual budget health summaries.\n"
    "- You can embed relevant illustrative animated GIF/image banners where helpful (e.g. for focus/productivity: https://media.giphy.com/media/3oKIPnAiaMCws8nOsE/giphy.gif, for finance: https://media.giphy.com/media/67ThRZlYBvibtdF9UC/giphy.gif, for wellness/habits: https://media.giphy.com/media/l41YfykEffZ7QM55m/giphy.gif).\n"
    "- Always conclude with an actionable recommendation or pro-tip to empower the user's day!"
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        list_memories,
        get_memory,
        save_memory,
        list_tasks,
        add_task,
        complete_task,
        log_expense,
        get_financial_summary,
        get_weather,
        get_current_time,
    ],
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
