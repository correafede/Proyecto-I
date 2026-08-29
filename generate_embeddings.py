"""
Generate and store embeddings for all documents in the database
"""

import os
import sys
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Documento
from embedding_service import get_embedding, normalize_embedding

def generate_all_embeddings():
    """Generate embeddings for all documents without embeddings."""
    
    db = SessionLocal()
    
    try:
        # Find documents without embeddings
        docs_to_embed = db.query(Documento).filter(Documento.embedding == None).all()
        
        if not docs_to_embed:
            print("✓ All documents already have embeddings!")
            return
        
        print(f"Generating embeddings for {len(docs_to_embed)} documents...\n")
        
        for i, doc in enumerate(docs_to_embed, 1):
            # Combine text fields for embedding
            text = f"{doc.titulo}. {doc.descripcion or ''}. {doc.palabras_clave or ''}"
            
            print(f"[{i}/{len(docs_to_embed)}] {doc.id_biblioteca}: {doc.titulo[:50]}...")
            
            # Generate embedding
            embedding = get_embedding(text)
            
            if embedding:
                # Normalize
                embedding = normalize_embedding(embedding)
                doc.embedding = embedding
                db.commit()
                print(f"   ✓ Embedding stored ({len(embedding)} dimensions)")
            else:
                print(f"   ✗ Failed to generate embedding")
        
        print(f"\n✓ Completed! {len(docs_to_embed)} documents embedded.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_all_embeddings()
