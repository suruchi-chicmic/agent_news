import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

load_dotenv()

# Setup local ChromaDB
# persist_path = "./chroma_db
# client = chromadb.PersistentClient(path=persist_path)
client = chromadb.Client() # This is ephemeral (temporary)

embedding_function = embedding_functions.DefaultEmbeddingFunction()

collection = client.get_or_create_collection(
    name="news_archive",
    embedding_function=embedding_function
)

def archive_summary(query: str, summary: str):
    """Stores a summary in the vector database."""
    collection.add(
        documents=[summary],
        metadatas=[{"query": query}],
        ids=[f"news_{query.replace(' ', '_')}_{os.urandom(4).hex()}"]
    )

def query_archive(query: str, n_results: int = 3):
    """Queries for relevant past summaries."""
    results = collection.query(query_texts=[query], n_results=n_results)
    return results["documents"][0] if results["documents"] else []

def get_all_history_topics():
    """Fetches all unique queries from the metadata."""
    all_data = collection.get(include=['metadatas'])
    if not all_data['metadatas']:
        return "No history found."
    topics = list(set([m['query'] for m in all_data['metadatas'] if 'query' in m]))
    return ", ".join(topics)