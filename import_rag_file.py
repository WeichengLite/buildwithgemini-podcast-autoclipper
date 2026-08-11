import vertexai
from vertexai.preview import rag

PROJECT_ID = "qwiklabs-gcp-04-1e4b1b5ba2ff"
LOCATION = "us-west1"
CORPUS_NAME = "projects/621130316736/locations/us-west1/ragCorpora/4611686018427387904"
GCS_PATH = "gs://podcast-autoclipper-assets-qwiklabs-gcp-04-1e4b1b5ba2ff/rag/podcast_playbook.txt"

print(f"Initializing Vertex AI in project '{PROJECT_ID}', location '{LOCATION}'...")
vertexai.init(project=PROJECT_ID, location=LOCATION)

print(f"Importing file '{GCS_PATH}' into corpus '{CORPUS_NAME}'...")
resp = rag.import_files(
    corpus_name=CORPUS_NAME,
    paths=[GCS_PATH],
    transformation_config=rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
    ),
)
print("Import completed! Imported files count:", resp.imported_rag_files_count)
