"""Seed script for Productivity (tasks) and Finance (expenses/budgets) collections in Firestore."""

from google.cloud import firestore
import datetime

PROJECT_ID = "qwiklabs-gcp-04-f4cdb9206689"
db = firestore.Client(project=PROJECT_ID)

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

# 1. Seed Tasks (Personal Productivity)
tasks_data = [
    {
        "id": "task_1",
        "title": "Draft Architecture Brief for Smart Tracker AI",
        "category": "work",
        "priority": "high",
        "estimated_minutes": 60,
        "due_date": today_str,
        "completed": False,
        "created_at": now,
        "updated_at": now,
    },
    {
        "id": "task_2",
        "title": "Review Q3 Personal Expense Budget",
        "category": "finance",
        "priority": "medium",
        "estimated_minutes": 30,
        "due_date": today_str,
        "completed": False,
        "created_at": now,
        "updated_at": now,
    },
    {
        "id": "task_3",
        "title": "Review Vertex AI Reasoning Engine logs",
        "category": "learning",
        "priority": "low",
        "estimated_minutes": 45,
        "due_date": today_str,
        "completed": True,
        "created_at": now,
        "updated_at": now,
    },
]

# 2. Seed Finance Records
finances_data = [
    {
        "id": "exp_1",
        "amount": 14.50,
        "category": "food",
        "description": "Lunch at healthy cafe",
        "date": today_str,
        "created_at": now,
    },
    {
        "id": "exp_2",
        "amount": 45.00,
        "category": "learning",
        "description": "Cloud Architecture Technical Book",
        "date": today_str,
        "created_at": now,
    },
    {
        "id": "exp_3",
        "amount": 12.00,
        "category": "transport",
        "description": "Subway transit card refill",
        "date": today_str,
        "created_at": now,
    },
]

print("Seeding tasks collection...")
for t in tasks_data:
    db.collection("tasks").document(t["id"]).set(t)
    print(f"  + Task: {t['title']} ({t['priority']})")

print("\nSeeding finances collection...")
for f in finances_data:
    db.collection("finances").document(f["id"]).set(f)
    print(f"  + Expense: ${f['amount']} - {f['description']} [{f['category']}]")

print("\nSeeding completed successfully!")
