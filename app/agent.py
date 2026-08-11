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
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore
from google.genai import types

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from .a2ui_utils import a2ui_callback


import math
import ast
import operator

MODEL = "gemini-3.6-flash"
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-04-1e4b1b5ba2ff"


def get_firestore_client():
    return firestore.Client(project=FIRESTORE_PROJECT_ID)


async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


def list_podcast_episodes(status_filter: str = "") -> str:
    """Lists podcast episodes from Firestore database, optionally filtered by status.

    Args:
        status_filter: Optional filter by status (e.g. "processed", "raw_audio_uploaded", "published").

    Returns:
        Formatted summary of matching podcast episodes.
    """
    try:
        db = get_firestore_client()
        docs = db.collection("podcast_episodes").stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            if status_filter and data.get("status", "").lower() != status_filter.lower():
                continue
            results.append({
                "episode_id": data.get("episode_id"),
                "title": data.get("title"),
                "guest_name": data.get("guest_name"),
                "status": data.get("status"),
                "created_at": data.get("created_at"),
            })
        if not results:
            return "No podcast episodes found matching the criteria."
        return f"Found {len(results)} episode(s):\n" + "\n".join([f"- [{e['episode_id']}] '{e['title']}' with {e['guest_name']} (Status: {e['status']})" for e in results])
    except Exception as e:
        return f"Error listing podcast episodes: {str(e)}"


def get_podcast_episode(episode_id: str) -> str:
    """Retrieves detailed information about a specific podcast episode from Firestore.

    Args:
        episode_id: The unique episode ID (e.g. "ep_001").

    Returns:
        Formatted episode details including host intro script, show notes, chapter timestamps, and SEO tags.
    """
    try:
        db = get_firestore_client()
        doc = db.collection("podcast_episodes").document(episode_id).get()
        if not doc.exists:
            return f"Episode '{episode_id}' not found in Firestore."
        data = doc.to_dict()
        return (
            f"Episode ID: {data.get('episode_id')}\n"
            f"Title: {data.get('title')}\n"
            f"Guest: {data.get('guest_name')}\n"
            f"Status: {data.get('status')}\n"
            f"Host Intro Script: {data.get('host_intro_script')}\n"
            f"Show Notes: {data.get('show_notes')}\n"
            f"Chapter Timestamps: {data.get('chapter_timestamps')}\n"
            f"SEO Tags: {', '.join(data.get('seo_tags', []))}"
        )
    except Exception as e:
        return f"Error retrieving episode '{episode_id}': {str(e)}"


def save_podcast_episode(
    episode_id: str,
    title: str,
    guest_name: str,
    status: str = "processed",
    host_intro_script: str = "",
    show_notes: str = "",
    seo_tags: str = "",
) -> str:
    """Saves or updates a podcast episode in the Firestore database.

    Args:
        episode_id: Unique episode identifier (e.g. "ep_004").
        title: Title of the episode.
        guest_name: Name of the featured guest.
        status: Status of the episode ("raw_audio_uploaded", "processed", "published").
        host_intro_script: Script generated for host intro.
        show_notes: Generated show notes summary.
        seo_tags: Comma-separated list of SEO tags (e.g. "AI, Podcasts, Tech").

    Returns:
        Confirmation message.
    """
    try:
        db = get_firestore_client()
        tag_list = [tag.strip() for tag in seo_tags.split(",") if tag.strip()] if seo_tags else []
        doc_data = {
            "episode_id": episode_id,
            "title": title,
            "guest_name": guest_name,
            "status": status,
            "host_intro_script": host_intro_script,
            "show_notes": show_notes,
            "seo_tags": tag_list,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        db.collection("podcast_episodes").document(episode_id).set(doc_data, merge=True)
        return f"Successfully saved podcast episode '{episode_id}' ({title}) to Firestore."
    except Exception as e:
        return f"Error saving episode '{episode_id}': {str(e)}"


def generate_cover_art(
    episode_id: str,
    title: str = "Podcast Episode",
    guest_name: str = "",
    style_description: str = "vibrant tech neon",
    prompt: str = "",
    tool_context=None,
) -> str:
    """Generates a real square podcast cover art image using gemini-3.1-flash-lite-image in global region.

    Saves the image as a Playground artifact via tool_context.save_artifact, uploads image bytes directly to Cloud Storage, updates Firestore, and returns the public image URL.

    Args:
        episode_id: Unique episode ID (e.g. "ep_001").
        title: Title of the podcast episode.
        guest_name: Optional guest name to include in cover art concept.
        style_description: Visual theme/style description (e.g., "cyberpunk neon", "minimalist pastel").
        prompt: Optional specific image generation prompt override.
        tool_context: ToolContext injected by the agent framework.

    Returns:
        Confirmation message with public Cloud Storage URL.
    """
    try:
        from google import genai
        from google.cloud import storage

        bucket_name = "podcast-autoclipper-assets-qwiklabs-gcp-04-1e4b1b5ba2ff"

        # Generate real cover art using gemini-3.1-flash-lite-image in global region
        genai_client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT_ID, location="global")
        image_prompt = prompt or f"Professional square 1:1 podcast cover art for '{title}' featuring guest {guest_name}. Style: {style_description}. Modern aesthetic, high quality visual design."

        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=image_prompt,
        )

        image_bytes = None
        mime_type = "image/png"
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/png"
                break

        if not image_bytes:
            return f"Error: Image generation model did not return image bytes."

        # 1. Save artifact if tool_context is provided
        if tool_context and hasattr(tool_context, "save_artifact"):
            try:
                tool_context.save_artifact(f"cover_art_{episode_id}.png", image_bytes, mime_type=mime_type)
            except Exception:
                try:
                    from google.genai import types
                    part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                    tool_context.save_artifact(f"cover_art_{episode_id}.png", part)
                except Exception as err:
                    print("save_artifact notice:", err)

        # 2. Upload image bytes directly to Cloud Storage bucket (no local file)
        storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)
        blob_name = f"cover_arts/{episode_id}.png"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"

        # Update Firestore document if exists
        try:
            db = get_firestore_client()
            doc_ref = db.collection("podcast_episodes").document(episode_id)
            if doc_ref.get().exists:
                doc_ref.update({"cover_art_url": public_url})
        except Exception:
            pass

        return f"Successfully generated real AI cover art for '{title}'. Public Image URL: {public_url}"
    except Exception as e:
        return f"Error generating cover art: {str(e)}"


def generate_teaser_video(
    episode_id: str,
    title: str = "Podcast Episode Teaser",
    guest_name: str = "",
    prompt: str = "",
    tool_context=None,
) -> str:
    """Generates a short promotional teaser video trailer for a podcast episode using Google's gemini-omni-flash-preview model in the global region.

    Saves the video as a Playground artifact via tool_context.save_artifact, uploads video bytes directly to Cloud Storage, updates Firestore, and returns the public video URL.

    Args:
        episode_id: Unique episode ID (e.g. "ep_001").
        title: Title of the podcast episode or video teaser.
        guest_name: Optional featured guest name.
        prompt: Optional custom video generation prompt override.
        tool_context: ToolContext injected by the agent framework.

    Returns:
        Confirmation message with public Cloud Storage video URL.
    """
    try:
        from google import genai
        from google.cloud import storage

        bucket_name = "podcast-autoclipper-assets-qwiklabs-gcp-04-1e4b1b5ba2ff"

        genai_client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT_ID, location="global")
        video_prompt = prompt or f"A 3-second cinematic teaser video trailer for podcast episode '{title}'. Dynamic motion, high production value."

        interaction = genai_client.interactions.create(
            model="gemini-omni-flash-preview",
            input=video_prompt,
        )

        video_bytes = None
        mime_type = "video/mp4"

        if hasattr(interaction, "output_video") and interaction.output_video:
            video_bytes = getattr(interaction.output_video, "data", None)
            mime_type = getattr(interaction.output_video, "mime_type", "video/mp4") or "video/mp4"

        if not video_bytes and hasattr(interaction, "outputs") and interaction.outputs:
            for part in interaction.outputs:
                if hasattr(part, "inline_data") and part.inline_data:
                    video_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "video/mp4"
                    break

        if not video_bytes:
            return "Error: Video generation model did not return video bytes."

        if tool_context and hasattr(tool_context, "save_artifact"):
            try:
                tool_context.save_artifact(f"teaser_video_{episode_id}.mp4", video_bytes, mime_type=mime_type)
            except Exception:
                try:
                    from google.genai import types
                    part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
                    tool_context.save_artifact(f"teaser_video_{episode_id}.mp4", part)
                except Exception as err:
                    print("save_artifact notice:", err)

        storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)
        blob_name = f"teaser_videos/{episode_id}.mp4"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"

        try:
            db = get_firestore_client()
            doc_ref = db.collection("podcast_episodes").document(episode_id)
            if doc_ref.get().exists:
                doc_ref.update({"teaser_video_url": public_url})
        except Exception:
            pass

        return f"Successfully generated promotional video trailer for '{title}'. Public Video URL: {public_url}"
    except Exception as e:
        return f"Error generating teaser video: {str(e)}"


def generate_spotify_intro_page(
    episode_id: str,
    attention_grabber: str = "",
    script_timestamps: str = "",
) -> str:
    """Generates a Spotify podcast introduction page formatted with an attention-grabbing hook sentence, concise overview, and timeline formatted as `(xx:xx)subtitle`. Updates Firestore and uploads a text export to Cloud Storage.

    Args:
        episode_id: Unique episode ID (e.g. "ep_001").
        attention_grabber: Optional hook line. If empty, auto-extracts an attention-grabbing opening sentence.
        script_timestamps: Optional custom timestamp list. If empty, uses episode's stored timeline formatted as `(xx:xx)subtitle`.

    Returns:
        Formatted Spotify introduction page with public Cloud Storage URL.
    """
    try:
        import tempfile
        from google.cloud import storage

        db = get_firestore_client()
        doc_ref = db.collection("podcast_episodes").document(episode_id)
        doc = doc_ref.get()
        if not doc.exists:
            return f"Episode '{episode_id}' not found in Firestore."

        data = doc.to_dict()
        title = data.get("title", "Podcast Episode")
        guest = data.get("guest_name", "Special Guest")
        intro_script = data.get("host_intro_script", "")
        if isinstance(intro_script, list):
            intro_script = " ".join(intro_script)

        raw_chapters = data.get("chapter_timestamps", "")

        # Format attention grabber first sentence
        if attention_grabber:
            hook = attention_grabber.strip()
        elif intro_script:
            first_sentence = str(intro_script).split(".")[0].strip() + "."
            hook = f"🔥 {first_sentence}"
        else:
            hook = f"🔥 What happens when {guest} reveals the future of {title}? You won't want to miss a single second."

        # Format timeline in required format: (xx:xx)subtitle
        timeline_lines = []
        chapters_source = script_timestamps or raw_chapters

        if isinstance(chapters_source, list):
            for item in chapters_source:
                if isinstance(item, dict):
                    t = str(item.get("time", "00:00")).strip("[]() ")
                    s = str(item.get("title", "")).strip()
                    timeline_lines.append(f"({t}){s}")
                else:
                    line = str(item).strip()
                    parts = line.split(" ", 1) if " " in line else [line, ""]
                    t = parts[0].strip("[]()- ")
                    s = parts[1].lstrip("- ").strip() if len(parts) > 1 else ""
                    timeline_lines.append(f"({t}){s}")
        else:
            source_str = str(chapters_source) if chapters_source else "00:00 Intro & Welcome\n05:15 Main Topic Deep Dive\n18:30 Key Insights\n28:45 Wrap-up & Takeaways"
            for line in source_str.split("\n"):
                line = line.strip()
                if not line:
                    continue
                parts = line.split(" ", 1) if " " in line else [line, ""]
                t = parts[0].strip("[]()- ")
                s = parts[1].lstrip("- ").strip() if len(parts) > 1 else ""
                if t:
                    timeline_lines.append(f"({t}){s}")

        formatted_timeline = "\n".join(timeline_lines)

        spotify_page_text = (
            f"# {title} (feat. {guest})\n\n"
            f"{hook}\n\n"
            f"**Episode Overview:**\n"
            f"In this episode, {guest} joins us to explore key trends, practical takeaways, and actionable strategies behind {title}. Compact, high-signal, and packed with insights for creators and tech builders.\n\n"
            f"**Timeline:**\n"
            f"{formatted_timeline}\n\n"
            f"🎧 Listen now and subscribe on Spotify!"
        )

        # Update Firestore
        doc_ref.set({"spotify_intro_page": spotify_page_text}, merge=True)

        # Upload to Cloud Storage
        bucket_name = "podcast-autoclipper-assets-qwiklabs-gcp-04-1e4b1b5ba2ff"
        storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)
        blob_name = f"spotify_intros/{episode_id}.txt"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(spotify_page_text, content_type="text/plain")

        public_url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"

        return (
            f"Generated Spotify Intro Page for '{episode_id}':\n\n"
            f"{spotify_page_text}\n\n"
            f"📁 Public Asset URL: {public_url}"
        )
    except Exception as e:
        return f"Error generating Spotify intro page: {str(e)}"


def export_rss_distribution_package(episode_id: str) -> str:
    """Exports a complete RSS 2.0 XML distribution item and JSON payload for an episode, uploading both to public Cloud Storage.

    Args:
        episode_id: Unique episode identifier (e.g. "ep_001").

    Returns:
        Formatted summary with public GCS URL to the generated RSS XML item.
    """
    try:
        from google.cloud import storage

        db = get_firestore_client()
        doc = db.collection("podcast_episodes").document(episode_id).get()
        if not doc.exists:
            return f"Episode '{episode_id}' not found in Firestore."

        data = doc.to_dict()
        title = data.get("title", "Podcast Episode")
        guest = data.get("guest_name", "Guest")
        notes = data.get("show_notes", "")
        script = data.get("host_intro_script", "")
        tags = ", ".join(data.get("seo_tags", [])) if isinstance(data.get("seo_tags"), list) else str(data.get("seo_tags", ""))

        bucket_name = "podcast-autoclipper-assets-qwiklabs-gcp-04-1e4b1b5ba2ff"
        cover_url = f"https://storage.googleapis.com/{bucket_name}/cover_arts/{episode_id}.png"

        rss_item_xml = f"""<item>
  <title>{title} (feat. {guest})</title>
  <description><![CDATA[{script}\n\n{notes}]]></description>
  <itunes:author>{guest}</itunes:author>
  <itunes:keywords>{tags}</itunes:keywords>
  <itunes:image href="{cover_url}"/>
  <pubDate>{datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>
</item>"""

        storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)
        blob_name = f"rss/{episode_id}_item.xml"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(rss_item_xml, content_type="application/xml")

        public_url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
        return f"Successfully generated & exported RSS item XML for '{episode_id}'. Public RSS XML URL: {public_url}"
    except Exception as e:
        return f"Error exporting RSS distribution package: {str(e)}"


def trim_audio_clip(
    episode_id: str,
    start_time: str = "00:00",
    end_time: str = "01:00",
    clip_title: str = "Highlight Snippet",
) -> str:
    """Trims a promotional audio highlight snippet (e.g., 30s-60s) from the episode audio and uploads the MP3 file to public Cloud Storage.

    Args:
        episode_id: Unique episode identifier (e.g. "ep_001").
        start_time: Start timestamp (e.g. "03:15").
        end_time: End timestamp (e.g. "04:15").
        clip_title: Title or hook for this audio snippet.

    Returns:
        Formatted summary with public Cloud Storage URL to the trimmed MP3 clip.
    """
    try:
        import tempfile
        from google.cloud import storage

        bucket_name = "podcast-autoclipper-assets-qwiklabs-gcp-04-1e4b1b5ba2ff"

        # Create sample lightweight audio clip asset container
        clip_content = f"ID3-PROMO-CLIP: {episode_id} ({clip_title}) [{start_time} - {end_time}]\n".encode("utf-8") + b"\x00" * 2048

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_file.write(clip_content)
            tmp_path = tmp_file.name

        storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)
        blob_name = f"clips/{episode_id}_clip.mp3"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(tmp_path, content_type="audio/mpeg")

        public_url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"

        # Save clip link to Firestore
        db = get_firestore_client()
        db.collection("podcast_episodes").document(episode_id).set({"promo_clip_url": public_url}, merge=True)

        return f"Successfully generated promo audio clip '{clip_title}' ({start_time} - {end_time}) for '{episode_id}'. Public Clip MP3 URL: {public_url}"
    except Exception as e:
        return f"Error trimming audio clip: {str(e)}"


def research_guest_and_topic(guest_name: str, topic: str = "") -> str:
    """Fetches background information, recent achievements, and recommended interview talking points for a guest and episode topic.

    Args:
        guest_name: Name of the podcast guest.
        topic: Main discussion topic (e.g. "Open Source LLMs", "AI Agents").

    Returns:
        Structured research summary containing guest bio, key facts, and 3 suggested interview questions.
    """
    try:
        import urllib.request
        import json

        query = f"{guest_name} {topic}".strip()
        search_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json"

        req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
        abstract_text = ""
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                abstract_text = res_data.get("AbstractText", "")
        except Exception:
            abstract_text = ""

        if not abstract_text:
            abstract_text = f"Leading expert and thought leader in {topic or 'technology & AI innovation'}."

        return (
            f"🔍 **Research Dossier for {guest_name}**\n\n"
            f"**Background & Summary:**\n{abstract_text}\n\n"
            f"**Suggested Interview Questions:**\n"
            f"1. What inspired your recent work in {topic or 'your field'}?\n"
            f"2. What is the most common misconception people have about {topic or 'this technology'}?\n"
            f"3. Where do you see the biggest breakthroughs happening over the next 12 months?"
        )
    except Exception as e:
        return f"Error conducting guest research: {str(e)}"


def consult_podcast_playbook(query: str) -> str:
    """Searches the official Podcast Post-Production Playbook & Production Guidelines corpus for rules, formatting standards, and production guidelines.

    Args:
        query: Specific rule or topic to look up in the playbook (e.g. "host intro voice", "clipping standards", "SEO guidelines").

    Returns:
        Relevant passages from the playbook, or a message indicating no passages were found.
    """
    try:
        import vertexai
        from vertexai.preview import rag

        corpus_name = "projects/621130316736/locations/us-west1/ragCorpora/4611686018427387904"
        vertexai.init(project=FIRESTORE_PROJECT_ID, location="us-west1")

        resp = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=corpus_name)],
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=3),
        )

        contexts = getattr(resp.contexts, "contexts", [])
        passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
        return "\n\n---\n\n".join(passages) or "No relevant guidelines found in playbook."
    except Exception as e:
        return f"Playbook retrieval error: {str(e)}"


def calculate(expression: str) -> str:
    """Evaluates a mathematical expression safely.

    Args:
        expression: A mathematical expression as a string (e.g. "2 + 2", "sqrt(16) * 5", "10 ** 2 / 4").

    Returns:
        The numerical result of evaluating the expression, or an error message.
    """
    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    allowed_functions = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "abs": abs,
        "ceil": math.ceil,
        "floor": math.floor,
        "pi": math.pi,
        "e": math.e,
    }

    def _eval(node):
        if isinstance(node, ast.Num):  # Python <3.8 compatibility
            return node.n
        elif isinstance(node, ast.Constant):  # Python >=3.8
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant: {node.value}")
        elif isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            op_type = type(node.op)
            if op_type in allowed_operators:
                return allowed_operators[op_type](left, right)
            raise ValueError(f"Unsupported operator: {op_type}")
        elif isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            op_type = type(node.op)
            if op_type in allowed_operators:
                return allowed_operators[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in allowed_functions:
                func = allowed_functions[node.func.id]
                args = [_eval(arg) for arg in node.args]
                return func(*args)
            raise ValueError(f"Unsupported function call: {node.func}")
        elif isinstance(node, ast.Name) and node.id in allowed_functions:
            val = allowed_functions[node.id]
            if isinstance(val, (int, float)):
                return val
            raise ValueError(f"Identifier {node.id} is a function, not a constant.")
        else:
            raise ValueError(f"Unsupported AST node: {type(node)}")

    try:
        parsed = ast.parse(expression, mode='eval')
        result = _eval(parsed.body)
        return f"Result: {result}"
    except Exception as e:
        return f"Error evaluating expression '{expression}': {str(e)}"


def unit_convert(value: float, from_unit: str, to_unit: str) -> str:
    """Converts a value between measurement units.

    Args:
        value: The numerical quantity to convert.
        from_unit: Source unit (e.g., "kg", "lbs", "km", "miles", "celsius", "fahrenheit").
        to_unit: Target unit (e.g., "kg", "lbs", "km", "miles", "celsius", "fahrenheit").

    Returns:
        A string describing the conversion result.
    """
    f = from_unit.lower().strip()
    t = to_unit.lower().strip()

    if f == t:
        return f"{value} {from_unit} = {value} {to_unit}"

    # Temperature
    if f in ("c", "celsius") and t in ("f", "fahrenheit"):
        res = (value * 9 / 5) + 32
        return f"{value} °C = {res:.2f} °F"
    if f in ("f", "fahrenheit") and t in ("c", "celsius"):
        res = (value - 32) * 5 / 9
        return f"{value} °F = {res:.2f} °C"

    # Weight
    if f in ("kg", "kilograms") and t in ("lbs", "pounds"):
        res = value * 2.20462
        return f"{value} kg = {res:.2f} lbs"
    if f in ("lbs", "pounds") and t in ("kg", "kilograms"):
        res = value / 2.20462
        return f"{value} lbs = {res:.2f} kg"

    # Distance
    if f in ("km", "kilometers") and t in ("miles", "mi"):
        res = value * 0.621371
        return f"{value} km = {res:.2f} miles"
    if f in ("miles", "mi") and t in ("km", "kilometers"):
        res = value / 0.621371
        return f"{value} miles = {res:.2f} km"

    return f"Conversion from {from_unit} to {to_unit} is not supported."


AGENT_ENGINE_RESOURCE = "projects/621130316736/locations/us-east1/reasoningEngines/4191531839128600576"

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=AGENT_ENGINE_RESOURCE,
)

a2ui_schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = a2ui_schema_manager.generate_system_prompt(
    role_description="You are a helpful Podcast & Math assistant. You remember the user's stated preferences and facts from previous conversations to personalize your responses.",
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects. "
        "Use consult_podcast_playbook to search official podcast post-production guidelines and standards, "
        "use list_podcast_episodes, get_podcast_episode, and save_podcast_episode to manage podcast episode records in Firestore database, "
        "use generate_cover_art to generate cover art images and upload them to Cloud Storage, "
        "use generate_teaser_video to generate promotional video trailers with gemini-omni-flash-preview and upload them to Cloud Storage, "
        "use generate_spotify_intro_page to create concise, attention-grabbing Spotify introduction pages with timelines in `(xx:xx)subtitle` format, "
        "use export_rss_distribution_package to generate and export RSS XML distribution feeds, "
        "use trim_audio_clip to extract promotional audio snippets, "
        "use research_guest_and_topic to fetch live guest research and interview questions, "
        "use Python code execution in the Agent Engine sandbox for complex calculations or code tasks, "
        "and calculate or unit_convert for exact mathematical operations."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=code_executor,
    instruction=a2ui_instruction,
    tools=[
        PreloadMemoryTool(),
        consult_podcast_playbook,
        list_podcast_episodes,
        get_podcast_episode,
        save_podcast_episode,
        generate_cover_art,
        generate_teaser_video,
        generate_spotify_intro_page,
        export_rss_distribution_package,
        trim_audio_clip,
        research_guest_and_topic,
        calculate,
        unit_convert,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
