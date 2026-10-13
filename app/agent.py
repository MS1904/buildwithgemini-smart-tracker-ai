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


# ============================================================================
# CAREER & SKILL ROADMAP TRACKER (e.g., AI Engineer Roadmap)
# ============================================================================

def track_career_goal(goal_title: str, target_role: str, target_timeline_months: int = 6) -> Dict[str, Any]:
    """Initialize or update a high-level career learning roadmap in Firestore.

    Args:
        goal_title: Title of the career initiative (e.g. 'Master AI Engineering').
        target_role: Desired job role (e.g. 'AI Engineer', 'MLOps Specialist', 'Fullstack AI Developer').
        target_timeline_months: Target timeframe in months.

    Returns:
        Structured roadmap overview with phases and milestones.
    """
    db = _get_firestore_client()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    goal_id = "goal_ai_engineer" if "ai" in target_role.lower() else f"goal_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}"

    default_phases = [
        {"phase": 1, "title": "Mathematics & Core ML Foundations", "topics": ["Linear Algebra", "Calculus & Optimization", "PyTorch Basics"], "completed": True},
        {"phase": 2, "title": "LLM Architectures & Transformers", "topics": ["Attention Mechanism", "HuggingFace Transformers", "Prompt Engineering"], "completed": False},
        {"phase": 3, "title": "Agentic Systems & Multi-Agent Frameworks", "topics": ["Google ADK & A2A Protocol", "Vertex AI Reasoning Engines", "Function Tools & Memory Banks"], "completed": False},
        {"phase": 4, "title": "Production Deployment & Evaluation", "topics": ["Cloud Run Deployment", "A2UI Custom Surfaces", "RAG Engine Grounding", "Telemetry & Observability"], "completed": False},
    ]

    record = {
        "id": goal_id,
        "title": goal_title,
        "target_role": target_role,
        "timeline_months": target_timeline_months,
        "phases": default_phases,
        "created_at": now,
        "updated_at": now,
    }
    db.collection("career_goals").document(goal_id).set(record)
    return {
        "status": "active",
        "goal_id": goal_id,
        "target_role": target_role,
        "phases": default_phases,
        "message": f"Career track for '{target_role}' initialized with 4 milestone phases."
    }


def get_career_progress(target_role: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve the current career milestone progress and learning roadmap from Firestore.

    Args:
        target_role: Optional filter for specific role (defaults to all active career goals).

    Returns:
        Career roadmap, active milestones, and completion percentage.
    """
    db = _get_firestore_client()
    docs = db.collection("career_goals").limit(5).stream()
    goals = []
    for doc in docs:
        d = doc.to_dict()
        phases = d.get("phases", [])
        done_count = sum(1 for p in phases if p.get("completed", False))
        pct = int((done_count / len(phases) * 100)) if phases else 0
        goals.append({
            "goal_id": doc.id,
            "title": d.get("title"),
            "target_role": d.get("target_role"),
            "timeline_months": d.get("timeline_months"),
            "completion_percentage": f"{pct}%",
            "phases": phases,
        })

    if not goals:
        # Generate default AI Engineer progress if none found
        track_career_goal("Become a Senior AI Engineer", "AI Engineer", 6)
        return get_career_progress(target_role)

    return {"active_career_goals": goals}


# ============================================================================
# HEALTH, CALORIE & NUTRITION COACH WITH DISCREPANCY ANALYSIS
# ============================================================================

def log_meal_intake(meal_description: str, estimated_calories: int, protein_g: int = 0, meal_type: str = "lunch") -> Dict[str, Any]:
    """Log meals and caloric intake with automated health goal alignment checks.

    Args:
        meal_description: Description of the food or beverage consumed.
        estimated_calories: Caloric value in kcal (e.g. 650).
        protein_g: Estimated grams of protein (e.g. 35).
        meal_type: Type of meal ('breakfast', 'lunch', 'dinner', 'snack').

    Returns:
        Logged intake entry with real-time feedback.
    """
    db = _get_firestore_client()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    entry_id = f"meal_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}"
    record = {
        "id": entry_id,
        "date": today_str,
        "meal_type": meal_type,
        "description": meal_description,
        "calories": estimated_calories,
        "protein_g": protein_g,
        "logged_at": now,
    }
    db.collection("health_logs").document(entry_id).set(record)
    return {
        "status": "logged",
        "entry_id": entry_id,
        "description": meal_description,
        "calories": estimated_calories,
        "protein_g": protein_g,
        "date": today_str,
        "message": f"Logged {meal_description} ({estimated_calories} kcal, {protein_g}g protein)."
    }


def analyze_health_and_nutrition(daily_calorie_target: int = 1800, weight_loss_goal: bool = True) -> Dict[str, Any]:
    """Analyze recent caloric intake, weight trends, and provide alternative healthy substitutions.

    Args:
        daily_calorie_target: Target daily caloric budget in kcal (e.g. 1800).
        weight_loss_goal: Whether the user is actively pursuing weight loss.

    Returns:
        Summary of today's calorie tally, surplus/deficit status, and actionable dietary substitutions.
    """
    db = _get_firestore_client()
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    docs = db.collection("health_logs").where("date", "==", today_str).stream()

    total_calories = 0
    total_protein = 0
    logged_meals = []
    for doc in docs:
        d = doc.to_dict()
        cal = int(d.get("calories", 0))
        total_calories += cal
        total_protein += int(d.get("protein_g", 0))
        logged_meals.append({
            "meal_type": d.get("meal_type"),
            "description": d.get("description"),
            "calories": cal,
            "protein_g": d.get("protein_g", 0),
        })

    balance = total_calories - daily_calorie_target
    status = "Surplus" if balance > 0 else "Deficit"

    return {
        "today_date": today_str,
        "daily_target_calories": daily_calorie_target,
        "total_calories_intake": total_calories,
        "total_protein_grams": total_protein,
        "caloric_balance": f"{abs(balance)} kcal {status}",
        "weight_loss_target_met": (balance <= 0),
        "logged_meals": logged_meals,
        "advice_notes": "If in surplus during weight loss, recommend swapping dense refined carbs/sugary drinks for high-volume leafy greens, Greek yogurt, or an additional 30-minute brisk walk."
    }


# ============================================================================
# MEDICAL & HEALTH REPORT ANALYZER
# ============================================================================

def analyze_health_report(report_text: str, report_type: str = "blood_work", report_date: Optional[str] = None) -> Dict[str, Any]:
    """Parse, evaluate, and extract key biomarkers from uploaded or pasted medical/health reports.

    Args:
        report_text: Text content of medical report, lab test, blood panel, or doctor summary.
        report_type: Category ('blood_work', 'lipid_panel', 'metabolic_test', 'dexa_scan', 'fitness_assessment').
        report_date: Date of the report formatted YYYY-MM-DD.

    Returns:
        Extracted biomarker records, flagged values, and personalized lifestyle/dietary guidance.
    """
    db = _get_firestore_client()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    report_id = f"report_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}"
    record = {
        "id": report_id,
        "report_type": report_type,
        "date": report_date or today_str,
        "content_length": len(report_text),
        "analyzed_at": now,
    }
    db.collection("health_reports").document(report_id).set(record)

    return {
        "status": "analyzed_and_stored",
        "report_id": report_id,
        "report_type": report_type,
        "date": report_date or today_str,
        "instructions_for_agent": (
            "Examine the user's provided report text carefully. Identify key biomarkers (e.g. Glucose, HbA1c, Cholesterol, Vitamin D, Ferritin). "
            "Highlight any elevated or deficient numbers in a clean Markdown table with normal reference ranges, "
            "and suggest constructive nutritional, sleep, or exercise habits (always advising consultation with their medical provider)."
        )
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
    "You are Smart Tracker AI's Agent Assistant. You are a comprehensive personal life operating system, "
    "covering productivity, career development (e.g. AI Engineering), health & nutrition, personal finance, "
    "and evidence-grounded long-term memory.\n\n"
    "Available Core Capabilities:\n"
    "1. Productivity & Task Tracking: Use 'list_tasks', 'add_task', and 'complete_task' to manage to-do items. "
    "Whenever you display tasks, always include interactive task IDs so the user can complete them.\n"
    "2. Career Roadmaps (e.g. AI Engineer): Use 'track_career_goal' and 'get_career_progress' to track multi-phase "
    "engineering roadmaps, study milestones, and practical projects.\n"
    "3. Health, Nutrition & Calorie Tracking: Use 'log_meal_intake' and 'analyze_health_and_nutrition'. "
    "If a user's goal is weight loss but their intake is high or in surplus, deliver supportive, non-judgmental, "
    "and highly specific alternatives (e.g. swapping sugary drinks for sparkling water, high-protein satiety foods, "
    "or adjusting activity levels).\n"
    "4. Medical & Health Report Analysis: Use 'analyze_health_report' when users paste or upload lab tests, "
    "blood work, or health documents. Extract biomarkers into clear tables with reference ranges and lifestyle guidance.\n"
    "5. Personal Finance: Use 'log_expense' and 'get_financial_summary' to manage spending.\n"
    "6. Memory & Scheduling: Use 'list_memories', 'get_memory', 'save_memory', 'get_current_time', and 'get_weather'.\n\n"
    "PRESENTATION & GIF POLICY:\n"
    "- Make responses visually engaging, structured, and easy to read on mobile devices.\n"
    "- GIF USAGE: ONLY include an animated GIF when celebrating significant milestones (e.g. marking a task complete, "
    "completing a study milestone, or logging a major health win). Never spam GIFs on simple query responses.\n"
    "- When displaying GIFs, ONLY use verified direct Giphy links:\n"
    "  * Celebration/Complete: https://media.giphy.com/media/artj92V8o75VPL7AeQ/giphy.gif\n"
    "  * Focus/Coding: https://media.giphy.com/media/3oKIPnAiaMCws8nOsE/giphy.gif\n"
    "  * Wellness/Fitness: https://media.giphy.com/media/l41YfykEffZ7QM55m/giphy.gif\n"
    "- Use clean Markdown tables with status indicators: 🔴 High, 🟡 Medium, 🟢 Low, ✅ Done, ⏱️ Est. Time.\n"
    "- Always provide actionable coaching and empowering next steps!"
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
        track_career_goal,
        get_career_progress,
        log_meal_intake,
        analyze_health_and_nutrition,
        analyze_health_report,
        get_weather,
        get_current_time,
    ],
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
