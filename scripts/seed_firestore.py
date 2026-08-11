"""Seed script for populating Firestore with sample podcast episodes."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-1e4b1b5ba2ff"  # Hardcoded GCP Project ID

def seed_database():
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("podcast_episodes")

    episodes = [
        {
            "episode_id": "ep_001",
            "title": "AI-Powered Agents with Gemini 2.5",
            "guest_name": "Dr. Sarah Chen",
            "status": "processed",
            "host_intro_script": "Welcome back to Tech Bytes! Today we sit down with Dr. Sarah Chen to discuss how Gemini 2.5 and agentic workflows are changing software development.",
            "show_notes": "In this episode, Dr. Sarah Chen shares insights into building autonomous agents, multimodal audio processing, and memory banks.",
            "chapter_timestamps": [
                {"time": "00:00", "title": "Introduction"},
                {"time": "05:15", "title": "Multimodal Audio with Gemini"},
                {"time": "18:40", "title": "Cross-Session Memory Banks"},
                {"time": "28:10", "title": "Q&A with Dr. Chen"},
            ],
            "seo_tags": ["AI", "Gemini", "Podcast", "SoftwareEngineering", "Agents"],
            "created_at": "2026-08-10T14:30:00Z",
        },
        {
            "episode_id": "ep_002",
            "title": "The Future of Open Source LLMs",
            "guest_name": "Alex Rivera",
            "status": "raw_audio_uploaded",
            "host_intro_script": "Hey everyone! Joining us on Tech Bytes today is Alex Rivera, open-source maintainer and AI researcher.",
            "show_notes": "Alex Rivera explores the state of open-source models, local inference, and developer tools.",
            "chapter_timestamps": [
                {"time": "00:00", "title": "Welcome Alex Rivera"},
                {"time": "08:30", "title": "Open Source vs Proprietary AI"},
                {"time": "22:00", "title": "Local Model Benchmarks"},
            ],
            "seo_tags": ["OpenSource", "MachineLearning", "TechBytes", "DevTools"],
            "created_at": "2026-08-11T09:15:00Z",
        },
        {
            "episode_id": "ep_003",
            "title": "Building Scalable Cloud Pipelines",
            "guest_name": "Priya Sharma",
            "status": "published",
            "host_intro_script": "On Tech Bytes today, Priya Sharma breaks down cloud architecture, serverless data pipelines, and cost optimization.",
            "show_notes": "Learn how to optimize cloud resources, set up automated CI/CD pipelines, and manage event-driven architectures.",
            "chapter_timestamps": [
                {"time": "00:00", "title": "Intro & Guest Welcome"},
                {"time": "04:45", "title": "Serverless Pipeline Design"},
                {"time": "15:20", "title": "Cost Optimization Strategies"},
            ],
            "seo_tags": ["CloudComputing", "DevOps", "Serverless", "Architecture"],
            "created_at": "2026-08-11T16:00:00Z",
        },
    ]

    for ep in episodes:
        doc_ref = collection_ref.document(ep["episode_id"])
        doc_ref.set(ep)
        print(f"Seeded episode: {ep['episode_id']} - {ep['title']}")

    print("Firestore database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
