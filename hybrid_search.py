"""
Hybrid search service — BM25 + Vector similarity
"""

from sqlalchemy import text, func
from sqlalchemy.orm import Session
from models import Documento
from typing import List, Tuple
from embedding_service import get_embedding, normalize_embedding
import numpy as np

def bm25_search(db: Session, query: str, limit: int = 10) -> List[Documento]:
    """
    BM25 full-text search (lexical).
    
    Args:
        db: Database session
        query: Search query
        limit: Max results
    
    Returns:
        List of matching documents ranked by relevance
    """
    sql = text("""
        SELECT d.*, 
               ts_rank(
                   to_tsvector('spanish', d.titulo || ' ' || COALESCE(d.descripcion, '') || ' ' || COALESCE(d.palabras_clave, '')),
                   plainto_tsquery('spanish', :query)
               ) as rank
        FROM documentos d
        WHERE to_tsvector('spanish', d.titulo || ' ' || COALESCE(d.descripcion, '') || ' ' || COALESCE(d.palabras_clave, '')) 
              @@ plainto_tsquery('spanish', :query)
        ORDER BY rank DESC
        LIMIT :limit
    """)
    
    results = db.execute(sql, {"query": query, "limit": limit}).fetchall()
    
    # Convert to Document objects
    docs = []
    for row in results:
        # Get full document from session
        doc = db.query(Documento).filter(Documento.id == row[0]).first()
        if doc:
            docs.append(doc)
    
    return docs


def vector_search(db: Session, query: str, limit: int = 10, threshold: float = 0.3) -> List[Documento]:
    """
    Semantic search using vector similarity (cosine distance).
    
    Args:
        db: Database session
        query: Search query
        limit: Max results
        threshold: Minimum similarity (0-1)
    
    Returns:
        List of matching documents ranked by similarity
    """
    # Generate query embedding
    query_embedding = get_embedding(query)
    if not query_embedding:
        return []
    
    query_embedding = normalize_embedding(query_embedding)
    
    # Vector similarity search (cosine distance)
    sql = text("""
        SELECT d.id, d.id_biblioteca, d.titulo, 
               1 - (d.embedding <=> :query_embedding) as similarity
        FROM documentos d
        WHERE d.embedding IS NOT NULL
        AND (1 - (d.embedding <=> :query_embedding)) > :threshold
        ORDER BY similarity DESC
        LIMIT :limit
    """)
    
    results = db.execute(sql, {
        "query_embedding": query_embedding,
        "threshold": threshold,
        "limit": limit
    }).fetchall()
    
    # Fetch full documents
    docs = []
    for row in results:
        doc = db.query(Documento).filter(Documento.id == row[0]).first()
        if doc:
            docs.append(doc)
    
    return docs


def hybrid_search(db: Session, query: str, limit: int = 10, 
                  bm25_weight: float = 0.4, vector_weight: float = 0.6,
                  vector_threshold: float = 0.2) -> List[Tuple[Documento, float]]:
    """
    Hybrid search combining BM25 (lexical) and vector (semantic) search.
    
    Args:
        db: Database session
        query: Search query
        limit: Max results to return
        bm25_weight: Weight for BM25 results (0-1)
        vector_weight: Weight for vector results (0-1)
        vector_threshold: Minimum vector similarity score
    
    Returns:
        List of (Document, combined_score) tuples, sorted by score
    """
    
    # Run both searches
    bm25_results = bm25_search(db, query, limit=limit * 2)
    vector_results = vector_search(db, query, limit=limit * 2, threshold=vector_threshold)
    
    # Score documents by combining both search methods
    doc_scores = {}
    
    # BM25 scoring (position-based: first = 1.0, last = 0.0)
    for i, doc in enumerate(bm25_results):
        score = bm25_weight * (1.0 - (i / max(len(bm25_results), 1)))
        doc_scores[doc.id] = score
    
    # Vector scoring (position-based: first = 1.0, last = 0.0)
    for i, doc in enumerate(vector_results):
        vector_score = vector_weight * (1.0 - (i / max(len(vector_results), 1)))
        doc_scores[doc.id] = doc_scores.get(doc.id, 0) + vector_score
    
    # Sort by combined score and return top results
    sorted_docs = sorted(
        [(db.query(Documento).filter(Documento.id == doc_id).first(), score) 
         for doc_id, score in doc_scores.items()],
        key=lambda x: x[1],
        reverse=True
    )[:limit]
    
    return [(doc, score) for doc, score in sorted_docs if doc is not None]
