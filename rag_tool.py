"""
RAG (Retrieval-Augmented Generation) memory.

Lets Jarvis actually know things from your own files, instead of just
its general training knowledge. Two ways to add knowledge:

1. Drop .txt or .md files into config.KNOWLEDGE_FOLDER, then say
   "index my notes" — it reads and remembers everything in there.
2. Say "remember [something]" — stores that one fact directly.

Uses Ollama's own embedding model (nomic-embed-text) and a local
ChromaDB database — everything stays on your PC.

Requires: pip install chromadb
          ollama pull nomic-embed-text
"""

import os
import requests
import config

_chroma_client = None
_collection = None


def _get_collection():
    global _chroma_client, _collection
    if _collection is not None:
        return _collection

    import chromadb
    db_path = os.path.join(config.PROJECT_DIR, "memory_db")
    _chroma_client = chromadb.PersistentClient(path=db_path)
    _collection = _chroma_client.get_or_create_collection("jarvis_memory")
    return _collection


def _embed(text: str):
    """Get an embedding vector for text using Ollama's embedding model."""
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={"model": config.EMBEDDING_MODEL, "prompt": text},
        timeout=120,  # first-time model load can be slow, especially alongside a loaded LLM
    )
    response.raise_for_status()
    return response.json()["embedding"]


def _chunk_text(text: str, chunk_size: int = 500) -> list:
    """Split long text into roughly chunk_size-character pieces."""
    words = text.split()
    chunks, current = [], []
    length = 0
    for word in words:
        current.append(word)
        length += len(word) + 1
        if length >= chunk_size:
            chunks.append(" ".join(current))
            current, length = [], 0
    if current:
        chunks.append(" ".join(current))
    return chunks


def index_knowledge_folder() -> str:
    """Read every .txt/.md file in config.KNOWLEDGE_FOLDER and remember it."""
    folder = config.KNOWLEDGE_FOLDER
    os.makedirs(folder, exist_ok=True)

    files = [f for f in os.listdir(folder) if f.lower().endswith((".txt", ".md"))]
    if not files:
        return (f"No .txt or .md files found in {folder} — drop some notes "
                f"there first, then say 'index my notes' again.")

    try:
        collection = _get_collection()
    except ImportError:
        return "RAG memory needs one more package — run `pip install chromadb` first."

    total_chunks = 0
    for filename in files:
        path = os.path.join(folder, filename)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        chunks = _chunk_text(text)
        for i, chunk in enumerate(chunks):
            try:
                embedding = _embed(chunk)
            except Exception as e:
                return f"Couldn't reach Ollama's embedding model: {e}. Run `ollama pull {config.EMBEDDING_MODEL}` first."
            collection.upsert(
                ids=[f"{filename}::{i}"],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{"source": filename}],
            )
            total_chunks += 1

    return f"Indexed {len(files)} file(s) into memory ({total_chunks} chunks total)."


def remember(fact: str) -> str:
    """Store a single fact directly, without needing a file."""
    try:
        collection = _get_collection()
    except ImportError:
        return "RAG memory needs one more package — run `pip install chromadb` first."

    try:
        embedding = _embed(fact)
    except Exception as e:
        return f"Couldn't reach Ollama's embedding model: {e}. Run `ollama pull {config.EMBEDDING_MODEL}` first."

    import time
    fact_id = f"manual::{int(time.time() * 1000)}"
    collection.upsert(
        ids=[fact_id],
        embeddings=[embedding],
        documents=[fact],
        metadatas=[{"source": "manually told"}],
    )
    return "Got it, I'll remember that."


def recall(question: str) -> str:
    """Search remembered knowledge and answer using it, citing the source."""
    try:
        collection = _get_collection()
    except ImportError:
        return "RAG memory needs one more package — run `pip install chromadb` first."

    if collection.count() == 0:
        return ("I don't have anything in memory yet — say 'remember [something]' "
                "or drop files in the knowledge folder and say 'index my notes'.")

    try:
        query_embedding = _embed(question)
    except Exception as e:
        return f"Couldn't reach Ollama's embedding model: {e}."

    results = collection.query(query_embeddings=[query_embedding], n_results=3)
    docs = results.get("documents", [[]])[0]
    sources = results.get("metadatas", [[]])[0]

    if not docs:
        return "I couldn't find anything relevant in what I remember."

    context = "\n\n".join(f"[From {m.get('source', 'unknown')}]: {d}" for d, m in zip(docs, sources))

    from llm import ask_llm
    prompt = (
        f"Answer the question using ONLY the context below. If the context "
        f"doesn't contain the answer, say you don't have that information "
        f"— don't make anything up.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}"
    )
    return ask_llm(prompt)