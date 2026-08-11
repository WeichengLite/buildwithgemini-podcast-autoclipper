# 🎙️ Podcast AutoClipper Studio

> **An AI-powered podcast post-production agent that transforms raw audio into complete publishable packages—show notes, timestamps, guest profiles, AI cover art, and Omni teaser video trailers.**

![Podcast AutoClipper Demo](demo.gif)

---

## 🚀 Overview

**Podcast AutoClipper** is an end-to-end podcast post-production automation agent built with the **Google Agent Development Kit (ADK)** and deployed on **Google Cloud Agent Platform**.

Podcast creators spend hours manually drafting show notes, timestamping key moments, creating social media teasers, and generating promotional graphics. Podcast AutoClipper automates the entire workflow from a single conversation or web dashboard action:

- 📝 **Show Notes & Timestamps**: Generates engaging 30-second host intros, guest profiles, key takeaways, and click-to-jump timeline markers.
- 🎨 **AI Cover Art Generation**: Creates custom, high-resolution square episode cover graphics matching guest topics.
- 🎬 **Omni Video Teasers**: Produces short promotional teaser videos using Google's **Omni Model** (`gemini-omni-flash-preview`).
- 🎵 **Spotify Intro Pages & RSS**: Generates Spotify-ready description copy and RSS feed distribution XML.
- 🖼️ **Interactive A2UI Cards**: Displays rich, interactive visual cards natively in the agent interface.

---

## ✨ Key Features

1. **Automated Post-Production Package**:
   - Single-click or prompt creation of host intro, guest background, chapter breakdown, and SEO tags.
2. **AI Visual & Video Studio**:
   - Integrated image generation for episode artwork.
   - Video trailer synthesis via `gemini-omni-flash-preview` in the global region.
3. **Cross-Session Memory Bank**:
   - Remembers host brand tone, recurring sponsors, episode structure preferences, and default formats across sessions.
4. **Knowledge Retrieval (RAG)**:
   - Grounded on `podcast_playbook.txt` via Vertex AI RAG Engine for strict adherence to branding and editorial standards.
5. **Multi-Channel Distribution Ready**:
   - Exports formatted Markdown transcripts, Spotify intro pages, and Cloud Storage asset URLs (`https://storage.googleapis.com/...`).
6. **Web Studio Dashboard**:
   - Includes a modern FastAPI proxy frontend featuring a dark/light mode toggle, active episode workspace selector, promotional media preview boxes, and real-time AI assistant console.

---

## ☁️ Google Cloud Tools & Architecture

| Google Cloud Service | Purpose in Podcast AutoClipper |
| :--- | :--- |
| **Vertex AI Memory Bank** | Persists host preferences, tone of voice, and brand guidelines across user sessions. |
| **Google GenAI / Omni Model (`gemini-omni-flash-preview`)** | Generates short video teaser trailers for podcast episodes. |
| **Imagen / Gemini Image Gen** | Generates custom 1:1 square cover art graphics for each episode. |
| **Vertex AI RAG Engine** | Grounding corpus built from `podcast_playbook.txt` for editorial guidelines. |
| **Cloud Storage (GCS)** | Public storage bucket hosting generated cover art, audio clips, and teaser video MP4s. |
| **Firestore** | NoSQL database storing episode state, metadata, and generated asset links (`podcast_episodes` collection). |
| **A2UI (Agent-to-User Interface)** | Protocol for rendering rich visual card surfaces in the UI. |
| **Agent Runtime / Reasoning Engine** | Managed, scalable backend hosting the ADK A2A agent runtime. |
| **Cloud Run** | Serverless platform running the FastAPI proxy frontend and Web Studio Dashboard. |

---

## 🛠️ Project Structure

```
podcast-autoclipper/
├── app/
│   ├── agent.py               # Core ADK agent, tools, memory callback, & A2UI prompt
│   └── __init__.py
├── frontend/
│   ├── main.py                # FastAPI proxy connecting browser to deployed A2A agent
│   ├── static/
│   │   └── index.html         # Modern Web Studio Dashboard UI
│   └── requirements.txt
├── scripts/
│   └── generate_demo_gif.py   # Script generating the animated demo GIF
├── podcast_playbook.txt       # RAG knowledge source for podcast editorial guidelines
├── demo.gif                   # Looping video preview of the Web Studio Dashboard
├── agents-cli-manifest.yaml   # Deployment metadata configuration
└── README.md                  # Project documentation
```

---

## 🏁 Getting Started

### 1. Prerequisites
Ensure you have the Google Cloud SDK and Python 3.11+ installed:
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Local Environment Setup
```bash
git clone <your-repo-url>
cd podcast-autoclipper
python3 -m venv .venv
source .venv/bin/python
pip install -r requirements.txt
```

### 3. Running the Web Studio Dashboard Locally
```bash
cd frontend
pip install -r requirements.txt
export AGENT_ENGINE_RESOURCE_NAME="projects/YOUR_PROJECT/locations/us-east1/reasoningEngines/YOUR_ENGINE_ID"
export AGENT_DIRECTORY="app"
python main.py
```
Open [http://localhost:8080](http://localhost:8080) in your browser to access the Web Studio Dashboard.

### 4. Deploying to Cloud
- **Agent Backend**:
  ```bash
  agents-cli deploy --project YOUR_PROJECT_ID --region us-east1
  ```
- **Frontend Service**:
  ```bash
  cd frontend
  gcloud run deploy podcast-autoclipper-frontend \
    --source . \
    --region us-east1 \
    --allow-unauthenticated \
    --set-env-vars AGENT_ENGINE_RESOURCE_NAME="...",AGENT_DIRECTORY="app"
  ```

---

## 📜 License
Licensed under the Apache 2.0 License.
