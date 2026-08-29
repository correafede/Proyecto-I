"""
Embedding service — Generate vector embeddings using Ollama
"""

import requests
import numpy as np
from typing import Optional

OLLAMA_API = "http://host.docker.internal:11434/api/embeddings"
MODEL = "nomic-embed-text"  # Free embedding model via Ollama

def get_embedding(text: str) -> Optional[list[float]]:
    """
    Generate embedding for text using Ollama.
    
    Args:
        text: Text to embed
    
    Returns:
        List of floats (embedding vector) or None on error
    """
    if not text or len(text.strip()) == 0:
        return None
    
    try:
        response = requests.post(
            OLLAMA_API,
            json={
                "model": MODEL,
                "prompt": text
            },
            timeout=30
        )
        
        response.raise_for_status()
        embedding = response.json()["embedding"]
        return embedding
        
    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to Ollama at {OLLAMA_API}")
        print("Make sure Ollama is running: ollama serve")
        return None
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def normalize_embedding(embedding: list[float]) -> list[float]:
    """Normalize embedding to unit vector (L2 norm)."""
    arr = np.array(embedding)
    norm = np.linalg.norm(arr)
    if norm > 0:
        return (arr / norm).tolist()
    return embedding


def batch_embeddings(texts: list[str], batch_size: int = 5) -> list[Optional[list[float]]]:
    """
    Generate embeddings for multiple texts.
    
    Args:
        texts: List of texts to embed
        batch_size: Number of parallel requests
    
    Returns:
        List of embeddings (may contain None for failures)
    """
    embeddings = []
    for i, text in enumerate(texts):
        print(f"[{i+1}/{len(texts)}] Generating embedding...", end="\r")
        emb = get_embedding(text)
        if emb:
            emb = normalize_embedding(emb)
        embeddings.append(emb)
    print()
    return embeddings
