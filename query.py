import argparse
import warnings
import logging
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# Suppress HuggingFace Hub warnings that clutter the CLI output
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub.*")
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

def main():
    # Setup CLI argument parsing
    parser = argparse.ArgumentParser(description="Query the Qdrant database for Telegram URLs.")
    parser.add_argument("query", type=str, help="The search query string")
    parser.add_argument("--top", "-k", type=int, default=3, help="Number of results to return (default: 3)")
    args = parser.parse_args()

    print(f"🔍 Searching: \"{args.query}\"")
    
    # Connect to Qdrant
    client = QdrantClient(url="http://localhost:6333")
    collection_name = "tg_urls"
    
    # Get total count
    try:
        total_entries = client.count(collection_name=collection_name).count
    except Exception as e:
        print(f"Error communicating with Qdrant: {e}")
        return

    # Load the embedding model (will be fast since it's already cached)
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    
    # Generate the vector for the search query
    query_vector = model.encode(args.query).tolist()

    # Query Qdrant
    search_result = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=args.top
    )

    print("─" * 70)
    for idx, point in enumerate(search_result.points):
        # Format the output identically to the example
        score = point.score
        payload = point.payload or {}
        
        date = payload.get("date", "Unknown")
        url = payload.get("original_url", "Unknown")
        desc = payload.get("description", "Unknown")

        print(f"#{idx + 1} score: {score:.3f}")
        print(f" date: {date}")
        print(f" url: {url}")
        print(f" desc: {desc}")
        print("─" * 70)

    print(f"Showing {len(search_result.points)} of {total_entries} entries.")

if __name__ == '__main__':
    main()