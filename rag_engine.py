import os
import chromadb
from chromadb.config import Settings
import logging

logger = logging.getLogger(__name__)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai

class GeminiEmbeddingFunction(chromadb.EmbeddingFunction):
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)

    def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
        # Generate embeddings for a list of documents
        embeddings = []
        for doc in input:
            try:
                # We use text-embedding-004 which is the recommended Gemini embedding model
                response = self.client.models.embed_content(
                    model="text-embedding-004",
                    contents=doc
                )
                embeddings.append(response.embeddings[0].values)
            except Exception as e:
                logger.error(f"Error generating embedding: {e}")
                # Fallback zero vector if embedding fails to prevent crash
                embeddings.append([0.0] * 768) 
        return embeddings

class RagEngine:
    def __init__(self):
        # Initialize persistent ChromaDB in the current directory
        db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        
        api_key = os.getenv("GEMINI_API_KEY")
        self.embedding_function = GeminiEmbeddingFunction(api_key=api_key) if api_key else None
        
        # We will use a single collection and clear it before adding new chunks
        # This keeps the DB lightweight for the daily run
        self.collection_name = "daily_transcript_chunks"
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def process_transcript(self, transcript_text):
        """Chunks the transcript, generates embeddings, and stores them in ChromaDB."""
        if not self.embedding_function:
            logger.error("GEMINI_API_KEY not configured. Cannot generate embeddings.")
            return False

        # Ensure we start fresh for the new video
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
        except Exception:
            pass # Collection might not exist yet

        collection = self.chroma_client.create_collection(
            name=self.collection_name, 
            embedding_function=self.embedding_function
        )

        # Chunk the transcript
        chunks = self.text_splitter.split_text(transcript_text)
        if not chunks:
            return False

        logger.info(f"Chunked transcript into {len(chunks)} pieces. Generating embeddings...")
        
        # Create IDs for the chunks
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        
        # Add to ChromaDB
        # ChromaDB handles batching internally, but for very large transcripts 
        # you might want to batch this manually. For typical YT videos, it's fine.
        try:
            collection.add(
                documents=chunks,
                ids=ids
            )
            logger.info("Successfully indexed transcript in ChromaDB.")
            return True
        except Exception as e:
            logger.error(f"Error during RAG processing: {e}")
            return False

    def semantic_search(self, query, n_results=3):
        """Searches the vector database for chunks relevant to the query."""
        try:
            collection = self.chroma_client.get_collection(
                name=self.collection_name, 
                embedding_function=self.embedding_function
            )
            
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # The documents are returned as a list of lists
            if results and 'documents' in results and results['documents']:
                documents = results['documents'][0]
                return "\n\n---\n\n".join(documents)
            return ""
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            return ""
