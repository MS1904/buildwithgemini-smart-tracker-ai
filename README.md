# Smart Tracker AI — Autonomous Personal Operating System & Life Agent

> An omni-device, privacy-conscious personal operating system powered by **Gemini 3.8 Flash** on Google Cloud Agent Platform. Built with voice speech-to-text input, talk-back sound readout, intelligent intent auto-detection, AI career tracking, health & calorie coaching, and medical lab report biomarker analysis.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Cloud%20Run-059669?style=for-the-badge&logo=googlecloud)](https://smart-tracker-ai-frontend-88951093419.us-central1.run.app)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github)](https://github.com/MS1904/buildwithgemini-smart-tracker-ai)

🔗 **Live Public Web Application**: [https://smart-tracker-ai-frontend-88951093419.us-central1.run.app](https://smart-tracker-ai-frontend-88951093419.us-central1.run.app)

![Smart Tracker AI Live Demo](./demo.gif)

---

## 🌟 What the Agent Does

Smart Tracker AI acts as a personal life and productivity assistant that helps users manage their focus habits, career goals, nutrition balance, and health diagnostics using **real, verified data**. Rather than acting as a generic conversational bot, it queries persistent preferences and routines stored in Google Cloud Firestore and deploys specialized function tools to generate realistic, evidence-based recommendations.

### 🚀 Key Features & Capabilities

1. **🎙️ Voice Speech-to-Text (STT) Input**:
   - Hands-free microphone button (`🎙️`) powered by the Web Speech API.
   - Speak commands or meal descriptions naturally on mobile or desktop; inputs are transcribed in real-time with continuous intent detection.

2. **🔊 Talk-Back Sound Read-Out (TTS)**:
   - Dedicated "🔊 Read Out" sound button attached to every agent response.
   - Automatically sanitizes markdown syntax to synthesize pleasant, crystal-clear speech readout on demand.

3. **✨ Smart Intent Auto-Detection + Manual Mode Switcher**:
   - **Auto Mode (Default)**: Dynamically analyzes user prompts in real-time as you type or submit. Instantly adapts prompt chips and header mode badges to match user context:
     - *AI Engineering / Transformers / Pytorch* $\rightarrow$ **🤖 AI Career Roadmap**
     - *Calories / Meals / Weight Loss / Swaps* $\rightarrow$ **🥗 Health & Calorie Coach**
     - *Blood tests / Glucose / HbA1c / Biomarkers* $\rightarrow$ **📄 Medical Report Lab**
     - *Tasks / Focus / Schedule / Routines* $\rightarrow$ **📋 Task & Focus Engine**
     - *Expenses / Budget / Burn rate* $\rightarrow$ **💳 Finance & Budgeting**
   - **Manual Override**: Allows the user to select and lock into any mode via the header dropdown.

4. **🤖 AI Engineer Career Roadmap & Milestone Tracker**:
   - 4-phase structured curriculum: Phase 1 Foundations $\rightarrow$ Phase 2 Attention & Transformer Architectures $\rightarrow$ Phase 3 Fine-Tuning (PEFT/LoRA) $\rightarrow$ Phase 4 Autonomous Multi-Agent Systems.
   - Calculates progress percentage, awards milestone achievements, and generates portfolio project sprints.

5. **🥗 Health & Calorie Coach with Smart Food Swaps**:
   - Logs meals, calculates calories and macronutrients against daily targets.
   - Automatically detects caloric surplus (e.g. fast food, pizza, soda) and suggests mitigation steps (post-meal walks, calorie-saving healthy food swaps).

6. **📄 Medical Report & Biomarker Analyzer**:
   - Interactive modal to paste raw lab panels or blood work (Fasting Glucose, HbA1c, Lipids, Vitamin D).
   - Formats results into structured comparative tables, flags abnormal levels against clinical reference intervals, and recommends lifestyle adjustments.

7. **📊 Live Life Dashboard with Animated KPI Progress Rings**:
   - Collapsible top bar with interactive SVG progress indicators:
     - **🔥 Daily Calorie Gauge**: Visual dynamic ring tracking active intake against targets (`1,450 / 2,100 kcal`).
     - **🎯 AI Career Milestone Meter**: Live phase progress (`50% Phase 2 Transformers`).
     - **⚡ Deep Focus Log**: Focus hours completed towards deep work goals (`3.0 / 4.0 hrs`).
     - **🔥 Habit Consistency Streak**: `7 Days Active` with celebratory triggers.

8. **⚔️ AI Coach Persona Selector (Dynamic Agent Attitude)**:
   - Instant personality switcher with custom prompt tuning:
     - **🌱 Supportive Mentor**: Warm, empathetic, and constructive.
     - **🎖️ Tough Love Drill Sergeant**: High-urgency, direct, and eliminates excuses!
     - **🧠 Silicon Valley Tech Lead**: Pragmatic, architectural, and algorithmic rigor.
     - **🩺 Clinical Scientist**: Evidence-based metabolic analysis and clinical accuracy.

9. **📷 Camera / Photo Meal & Lab Report Uploader**:
   - Dedicated camera button (`📷`) next to voice input for attaching photos of meals or blood panels with automatic visual intent parsing.

10. **🎉 Celebration Confetti & Synthesized Web Audio Completion Chimes**:
    - Real-time `canvas-confetti` explosion and two-tone rising Web Audio harmonic chimes whenever a task is marked complete or a habit milestone is reached.

11. **📥 1-Click "Daily Executive Briefing" Export**:
    - Generates and downloads a clean, beautifully formatted Markdown summary containing dashboard metrics, coach guidance, and completed daily goals.

12. **📱 Omni-Device Responsive Design**:
    - Flawless user experience on smartphones (iOS safe areas, `100dvh` address bar handling), tablets, and ultrawide desktop monitors.
    - 4 selectable themes: **🌿 Emerald** (Default), **🌙 Midnight Dark**, **⚡ Cyberpunk Neon**, and **🌊 Oceanic Blue**.

---

## 🛠️ Implemented Function Tools

The backend agent code in [`app/agent.py`](app/agent.py) registers the following tools on Vertex AI Reasoning Engine:

| Tool | Description |
| :--- | :--- |
| **`track_career_goal`** | Updates career milestone tasks, tracks learning objectives (e.g. Transformers, PyTorch, LoRA), and calculates roadmap progress %. |
| **`get_career_progress`** | Returns active career stage, completed milestones, current phase, and next recommended project sprint. |
| **`log_meal_intake`** | Records meals, calories, and macronutrients (protein, carbs, fats) for daily intake tracking. |
| **`analyze_health_and_nutrition`** | Evaluates daily caloric balance against weight loss goals and generates alternative foods/steps when surplus is detected. |
| **`analyze_health_report`** | Analyzes clinical lab reports, extracts biomarker values (HbA1c, glucose, cholesterol, vitamins), and highlights out-of-range indicators. |
| **`list_memories`** / **`get_memory`** / **`save_memory`** | Reads and writes user preferences, routines, and peak focus windows to Google Cloud Firestore. |
| **`get_weather`** / **`get_current_time`** | Provides real-time weather and timezone data for contextual routine scheduling. |
| **`a2ui_callback`** | Transforms turns into rich A2UI cards, columns, and rows over the A2A protocol. |

---

## ☁️ Google Cloud Infrastructure

| Service | Component & Role | Status |
| :--- | :--- | :--- |
| **Vertex AI Agent Engine (Reasoning Engine)** | Deploys containerized ADK agent serving the **A2A (Agent-to-Agent)** protocol (`agents-cli-manifest.yaml`). | **Live** |
| **Gemini 3.8 Flash (`gemini-3.8-flash`)** | High-speed multimodal LLM reasoning engine via Google GenAI SDK. | **Live** |
| **Cloud Run** | Scalable, serverless hosting for the FastAPI proxy and mobile-responsive frontend. | **Live** |
| **Cloud Firestore (Native Mode)** | Persistent database storing user memories and routines in the `memories` collection. | **Live** |
| **Cloud Storage** | Public storage bucket (`gs://smart-tracker-ai-assets-f4cdb9`) configured for asset delivery. | **Live** |

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│  Smart Tracker Web Frontend                            │
│  - Web Speech STT (Mic) & TTS (Sound Readout)          │
│  - Auto-Intent Detector & Manual Mode Selector         │
│  - 4 Themes (Emerald, Dark, Cyberpunk, Oceanic)        │
│  - Interactive Medical Report & Capabilities Modals    │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP POST (/chat)
┌──────────────────────────▼─────────────────────────────┐
│  FastAPI A2A Proxy (frontend/main.py on Cloud Run)     │
│  Authenticates with Google Application Default Creds   │
└──────────────────────────┬─────────────────────────────┘
                           │ A2A Protocol (JSON-RPC 2.0)
┌──────────────────────────▼─────────────────────────────┐
│  Vertex AI Reasoning Engine                            │
│  - Model: Gemini 3.8 Flash                             │
│  - Agent: app/agent.py (ADK Root Agent)                │
│  - Tools: Career, Nutrition, Medical, Firestore        │
└──────────┬───────────────────────────────┬─────────────┘
           │                               │
    list/get/save                          │
           ▼                               ▼
┌──────────────────────┐        ┌────────────────────────┐
│ Google Cloud         │        │ Google Cloud           │
│ Firestore            │        │ Storage (Assets Bucket)│
└──────────────────────┘        └────────────────────────┘
```

---

## 🚀 Setup & Local Run Instructions

### Prerequisites
- Python 3.11+
- Google Cloud SDK (`gcloud`) authenticated with your project:
  ```bash
  gcloud auth application-default login
  gcloud config set project <YOUR_PROJECT_ID>
  ```

### 1. Install Dependencies
```bash
pip install -e .
pip install -r frontend/requirements.txt
```

### 2. Seed Firestore Memories (Optional / First Run)
```bash
python seed_firestore.py
```

### 3. Run Locally with ADK Web
```bash
adk web --port 8080 --allow_origins "*" --reload_agents
```

### 4. Run the Full Frontend Proxy
```bash
export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_NUMBER>/locations/us-central1/reasoningEngines/<REASONING_ENGINE_ID>"
export AGENT_DIRECTORY="app"

cd frontend
python main.py
```
Open `http://localhost:8080/` in your browser.

---

## 📄 License
Copyright 2026 Google LLC. Licensed under the Apache License, Version 2.0.
