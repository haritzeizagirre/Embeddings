import json
import sys
import os
import uuid
import glob
import warnings
import logging
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Suppress HuggingFace Hub warnings
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub.*")
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

def main():
    if len(sys.argv) < 2:
        files = glob.glob(os.path.join("backup", "parsed_urls_*.json"))
        if not files:
            print("Usage: python ingest_qdrant.py <path_to_parsed_json_file>")
            sys.exit(1)
        input_file = sorted(files)[-1]
        print(f"No file supplied. Auto-selected latest parsed urls file: {input_file}")
    else:
        input_file = sys.argv[1]
        
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    print(f"Loading '{input_file}'...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not data:
        print("No data found in the JSON file.")
        return

    # 1. Connect to Qdrant (which we have running locally on port 6333 via Docker)
    print("Connecting to Qdrant at localhost:6333...")
    client = QdrantClient(url="http://localhost:6333")
    collection_name = "tg_urls"

    # 2. Setup the Collection
    # recreate_collection drops the collection if it exists and creates a new one
    print(f"Configuring/Recreating Qdrant collection: '{collection_name}'...")
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=384,  # BAAI/bge-small-en-v1.5 produces 384-dimensional embeddings
            distance=models.Distance.COSINE
        )
    )

    # 3. Load the BGE-small Embedding Model
    print("Loading the BGE-small model (this will be cached after the first download)...")
    # 'BAAI/bge-small-en-v1.5' is an excellent lightweight model for semantic search
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    # 4. Generate Embeddings
    print(f"Generating embeddings for {len(data)} items...")
    # We will embed the 'description' field as it contains the main context/tweet body/page title
    texts_to_embed = [item.get('description', '') for item in data]
    
    # model.encode supports batch encoding and gives a progress bar
    embeddings = model.encode(texts_to_embed, show_progress_bar=True)

    # 5. Prepare Points & Upsert
    print("Preparing data points for Qdrant...")
    points = []
    for idx, item in enumerate(data):
        # We assign a random UUID for each point
        point_id = str(uuid.uuid4())
        
        points.append(
            models.PointStruct(
                id=point_id,
                vector=embeddings[idx].tolist(),
                payload=item  # The payload stores original_url, date, and description so we can retrieve them later
            )
        )

    print("Upserting to Qdrant...")
    # We can upsert all points in one go using the client
    client.upsert(
        collection_name=collection_name,
        points=points
    )

    print(f"\nSuccessfully stored {len(points)} URLs as vector embeddings in Qdrant!")

if __name__ == '__main__':
    main()