import os
import chromadb
from chromadb.config import Settings
import json

def view_chromadb_data():
    # Connect to the local ChromaDB
    db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
    if not os.path.exists(db_path):
        print(f"Error: No ChromaDB found at {db_path}")
        return

    chroma_client = chromadb.PersistentClient(path=db_path)
    collection_name = "daily_transcript_chunks"
    
    try:
        collection = chroma_client.get_collection(name=collection_name)
    except Exception as e:
        print(f"Could not load collection '{collection_name}': {e}")
        return

    # Fetch the first 2 items (so we don't spam the console)
    data = collection.peek(limit=2)
    
    print("\n--- ChromaDB Raw Data Structure (First 2 Chunks) ---")
    
    # We will print the lengths of the embeddings rather than the raw arrays
    # because a 768-dimensional float array is too large for the terminal.
    
    for i in range(len(data['ids'])):
        print(f"\n[ID]: {data['ids'][i]}")
        print(f"[Document/Text Chunk]:\n{data['documents'][i]}")
        
        # Display the length of the embedding array
        embedding = data['embeddings'][i]
        print(f"\n[Vector Embedding Length]: {len(embedding)} dimensions")
        print(f"[Sample Vector Data]: {embedding[:5]} ... (truncated)")
        print("-" * 50)

if __name__ == "__main__":
    view_chromadb_data()
