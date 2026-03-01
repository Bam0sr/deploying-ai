"""Service 2: semantic recipe search (ChromaDB)."""

import os
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langchain.tools import tool
from utils.logger import get_logger

_logs = get_logger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(SCRIPT_DIR, "data", "chroma_db")

_embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
_client = chromadb.PersistentClient(path=CHROMA_DIR)
_collection = _client.get_collection(name="recipes", embedding_function=_embedding_fn)


@tool
def search_recipes(query: str, n_results: int = 3) -> str:
    """searches the recipe knowledge base using semantic similarity.

    when the user asks open-ended cooking questions like
    'What is a good comfort food?', 
    'Suggest a vegetarian Italian dish',
    'What can I make with potatoes?'  
    --> Returns the most relevant recipes
    from the embedded recipe corpus.
    """
    _logs.info(f"[RAG] Searching recipes for: '{query}'")
    results = _collection.query(query_texts=[query], n_results=n_results)

    if not results["documents"] or not results["documents"][0]:
        _logs.info("[RAG] No matching recipes found.")
        return "No matching recipes found in the knowledge base."

    output_parts = []
    for idx, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][idx] if results["metadatas"] else {}
        dist = results["distances"][0][idx] if results.get("distances") else None
        name = meta.get("name", "Unknown")
        _logs.info(f"[RAG] Match {idx + 1}: {name} (distance: {dist:.3f})")
        header = f"Match {idx + 1}"
        if meta.get("name"):
            header += f" — {meta['name']}"
        if dist is not None:
            header += f" (similarity distance: {dist:.3f})"
        output_parts.append(f"{header}\n{doc}")

    return "\n\n---\n\n".join(output_parts)
