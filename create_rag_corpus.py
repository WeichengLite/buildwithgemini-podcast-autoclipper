import os
import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-04-1e4b1b5ba2ff"
LOCATION = "us-central1"
GCS_PATH = "gs://podcast-autoclipper-assets-qwiklabs-gcp-04-1e4b1b5ba2ff/rag/podcast_playbook.txt"

print(f"Initializing Vertex AI RAG Engine in project '{PROJECT_ID}', location '{LOCATION}'...")
vertexai.init(project=PROJECT_ID, location=LOCATION)

# 1. Switch the region's RAG managed DB to serverless mode
cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
try:
    rag.update_rag_engine_config(rag_engine_config=rag.RagEngineConfig(
        name=cfg,
        rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
    ))
    print("Updated RAG Engine config to serverless mode.")
except Exception as e:
    print(f"Notice on update_rag_engine_config: {e}")

# 2. Create serverless RAG corpus
print("Creating serverless RAG corpus...")
corpus = rag.create_corpus(
    display_name="podcast-playbook-corpus",
    embedding_model_config=rag.EmbeddingModelConfig(
        publisher_model="publishers/google/models/text-embedding-005"
    ),
)
print("CREATED_CORPUS_NAME:", corpus.name)

# 3. Import and index document
print(f"Importing document from '{GCS_PATH}' into corpus...")
PARSING_PROMPT = (
    "Extract key rules, formatting guidelines, and post-production standards for podcast episodes. "
    "Output clean, self-contained prose."
)

resp = rag.import_files(
    corpus_name=corpus.name,
    paths=[GCS_PATH],
    transformation_config=rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
    ),
    llm_parser=rag.LlmParserConfig(
        model_name="gemini-2.5-flash",
        custom_parsing_prompt=PARSING_PROMPT
    ),
)
print("Import complete! Imported file count:", resp.imported_rag_files_count)
