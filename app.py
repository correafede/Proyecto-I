"""
FastAPI application — Biblioteca de Seguridad de Procesos
REST API for document management, search, and RBPS element classification.
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import os

from database import SessionLocal
from models import Documento, ElementoRBPS, TipoDocumento, DocumentoRelacionado
from prompts import SYSTEM_PROMPT, build_user_prompt
from llm_service import call_llm, validate_citations
from hybrid_search import hybrid_search

# ============ Pydantic Schemas ============

class ElementoRBPSSchema(BaseModel):
    id: int
    nombre: str
    pilar: str
    
    class Config:
        from_attributes = True


class TipoDocumentoSchema(BaseModel):
    id: int
    nombre: str
    
    class Config:
        from_attributes = True


class DocumentoResponseSchema(BaseModel):
    id: int
    id_biblioteca: str
    titulo: str
    autor: str
    empresa: str
    fecha: Optional[str]
    tipo: TipoDocumentoSchema
    elemento_rbps_principal: Optional[ElementoRBPSSchema]
    palabras_clave: Optional[str]
    descripcion: Optional[str]
    grupo_origen: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentoCreateSchema(BaseModel):
    id_biblioteca: str
    titulo: str
    autor: str
    empresa: str
    fecha: Optional[str] = None
    tipo_id: int
    elemento_rbps_principal_id: Optional[int] = None
    palabras_clave: Optional[str] = None
    descripcion: Optional[str] = None
    notas: Optional[str] = None


class DocumentoRelacionadoSchema(BaseModel):
    id: int
    documento_origen_id: int
    documento_destino_id: int
    tipo_relacion: str
    
    class Config:
        from_attributes = True


class PreguntaAsistenteSchema(BaseModel):
    pregunta: str
    umbral_relevancia: float = 0.3  # Minimum score to consider a doc relevant
    
    class Config:
        from_attributes = True


class RespuestaAsistenteSchema(BaseModel):
    respuesta: str
    citas: list[str]
    informacion_insuficiente: bool
    confianza: float
    documentos_fuente: list[DocumentoResponseSchema]
    validacion_citas: dict
    
    class Config:
        from_attributes = True


# ============ FastAPI App ============

app = FastAPI(
    title="Biblioteca de Seguridad de Procesos API",
    description="Backend para gestión de documentos técnicos de seguridad de procesos",
    version="1.0.0"
)


def get_db():
    """Dependency: get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============ RBPS Elements ============

@app.get("/rbps-elementos/", response_model=list[ElementoRBPSSchema])
def listar_elementos_rbps(
    pilar: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all RBPS elements, optionally filtered by pillar."""
    query = db.query(ElementoRBPS)
    if pilar:
        query = query.filter(ElementoRBPS.pilar.contains(pilar))
    return query.order_by(ElementoRBPS.pilar, ElementoRBPS.nombre).all()


@app.get("/rbps-elementos/{elemento_id}", response_model=ElementoRBPSSchema)
def obtener_elemento_rbps(elemento_id: int, db: Session = Depends(get_db)):
    """Get a single RBPS element by ID."""
    elem = db.query(ElementoRBPS).filter(ElementoRBPS.id == elemento_id).first()
    if not elem:
        raise HTTPException(status_code=404, detail="Elemento RBPS no encontrado")
    return elem


# ============ Document Types ============

@app.get("/tipos-documento/", response_model=list[TipoDocumentoSchema])
def listar_tipos_documento(db: Session = Depends(get_db)):
    """List all document types."""
    return db.query(TipoDocumento).order_by(TipoDocumento.nombre).all()


# ============ Documents ============

@app.get("/documentos/", response_model=list[DocumentoResponseSchema])
def listar_documentos(
    tipo: Optional[str] = Query(None, description="Filter by document type name"),
    empresa: Optional[str] = Query(None, description="Filter by company"),
    autor: Optional[str] = Query(None, description="Filter by author"),
    elemento_rbps_id: Optional[int] = Query(None, description="Filter by RBPS element ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List documents with filters.
    
    Query params:
    - tipo: document type name (e.g., 'HAZOP', 'LOPA', 'Informe de Incidente')
    - empresa: company name
    - autor: author name
    - elemento_rbps_id: primary RBPS element ID
    """
    query = db.query(Documento)
    
    if tipo:
        query = query.join(TipoDocumento).filter(TipoDocumento.nombre.ilike(f"%{tipo}%"))
    if empresa:
        query = query.filter(Documento.empresa.ilike(f"%{empresa}%"))
    if autor:
        query = query.filter(Documento.autor.ilike(f"%{autor}%"))
    if elemento_rbps_id:
        query = query.filter(Documento.elemento_rbps_principal_id == elemento_rbps_id)
    
    return query.order_by(Documento.id_biblioteca).offset(skip).limit(limit).all()


@app.get("/documentos/{id_biblioteca}", response_model=DocumentoResponseSchema)
def obtener_documento(id_biblioteca: str, db: Session = Depends(get_db)):
    """Get a document by library ID (e.g., 'A1', 'H1', 'L2', 'M1')."""
    doc = db.query(Documento).filter(Documento.id_biblioteca == id_biblioteca).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc


@app.post("/documentos/", response_model=DocumentoResponseSchema)
def crear_documento(doc_data: DocumentoCreateSchema, db: Session = Depends(get_db)):
    """Create a new document."""
    # Check if already exists
    existing = db.query(Documento).filter(Documento.id_biblioteca == doc_data.id_biblioteca).first()
    if existing:
        raise HTTPException(status_code=400, detail="Documento con ese ID ya existe")
    
    # Verify type exists
    tipo = db.query(TipoDocumento).filter(TipoDocumento.id == doc_data.tipo_id).first()
    if not tipo:
        raise HTTPException(status_code=400, detail="Tipo de documento no existe")
    
    # Verify RBPS element if provided
    elemento = None
    if doc_data.elemento_rbps_principal_id:
        elemento = db.query(ElementoRBPS).filter(
            ElementoRBPS.id == doc_data.elemento_rbps_principal_id
        ).first()
        if not elemento:
            raise HTTPException(status_code=400, detail="Elemento RBPS no existe")
    
    doc = Documento(
        id_biblioteca=doc_data.id_biblioteca,
        titulo=doc_data.titulo,
        autor=doc_data.autor,
        empresa=doc_data.empresa,
        fecha=doc_data.fecha,
        tipo=tipo,
        elemento_rbps_principal=elemento,
        palabras_clave=doc_data.palabras_clave,
        descripcion=doc_data.descripcion,
        notas=doc_data.notas,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@app.put("/documentos/{id_biblioteca}", response_model=DocumentoResponseSchema)
def actualizar_documento(
    id_biblioteca: str,
    doc_data: DocumentoCreateSchema,
    db: Session = Depends(get_db)
):
    """Update a document."""
    doc = db.query(Documento).filter(Documento.id_biblioteca == id_biblioteca).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Update fields
    doc.titulo = doc_data.titulo
    doc.autor = doc_data.autor
    doc.empresa = doc_data.empresa
    doc.fecha = doc_data.fecha
    doc.palabras_clave = doc_data.palabras_clave
    doc.descripcion = doc_data.descripcion
    doc.notas = doc_data.notas
    
    if doc_data.tipo_id:
        tipo = db.query(TipoDocumento).filter(TipoDocumento.id == doc_data.tipo_id).first()
        if tipo:
            doc.tipo = tipo
    
    if doc_data.elemento_rbps_principal_id:
        elemento = db.query(ElementoRBPS).filter(
            ElementoRBPS.id == doc_data.elemento_rbps_principal_id
        ).first()
        if elemento:
            doc.elemento_rbps_principal = elemento
    
    db.commit()
    db.refresh(doc)
    return doc


@app.delete("/documentos/{id_biblioteca}")
def eliminar_documento(id_biblioteca: str, db: Session = Depends(get_db)):
    """Delete a document."""
    doc = db.query(Documento).filter(Documento.id_biblioteca == id_biblioteca).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Delete related records
    db.query(DocumentoRelacionado).filter(
        (DocumentoRelacionado.documento_origen_id == doc.id) |
        (DocumentoRelacionado.documento_destino_id == doc.id)
    ).delete()
    
    db.delete(doc)
    db.commit()
    return {"deleted": id_biblioteca}


# ============ Document Relationships ============

@app.get("/documentos/{id_biblioteca}/relacionados/", response_model=dict)
def obtener_documentos_relacionados(id_biblioteca: str, db: Session = Depends(get_db)):
    """Get documents related to a given document."""
    doc = db.query(Documento).filter(Documento.id_biblioteca == id_biblioteca).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Relationships FROM this document
    desde = db.query(DocumentoRelacionado).filter(
        DocumentoRelacionado.documento_origen_id == doc.id
    ).all()
    
    # Relationships TO this document
    hacia = db.query(DocumentoRelacionado).filter(
        DocumentoRelacionado.documento_destino_id == doc.id
    ).all()
    
    return {
        "documento": id_biblioteca,
        "relaciona_con": [
            {
                "id_biblioteca": r.documento_destino.id_biblioteca,
                "titulo": r.documento_destino.titulo,
                "tipo_relacion": r.tipo_relacion
            }
            for r in desde
        ],
        "relacionado_desde": [
            {
                "id_biblioteca": r.documento_origen.id_biblioteca,
                "titulo": r.documento_origen.titulo,
                "tipo_relacion": r.tipo_relacion
            }
            for r in hacia
        ]
    }


# ============ Search & Stats ============

@app.get("/buscar/")
def buscar(
    q: str = Query(..., min_length=1, description="Search term"),
    db: Session = Depends(get_db)
):
    """Search across document titles, descriptions, and keywords."""
    docs = db.query(Documento).filter(
        (Documento.titulo.ilike(f"%{q}%")) |
        (Documento.descripcion.ilike(f"%{q}%")) |
        (Documento.palabras_clave.ilike(f"%{q}%")) |
        (Documento.autor.ilike(f"%{q}%")) |
        (Documento.empresa.ilike(f"%{q}%"))
    ).all()
    
    return {
        "query": q,
        "resultados": len(docs),
        "documentos": [
            {
                "id_biblioteca": d.id_biblioteca,
                "titulo": d.titulo,
                "tipo": d.tipo.nombre,
                "autor": d.autor,
            }
            for d in docs
        ]
    }


@app.get("/estadisticas/")
def obtener_estadisticas(db: Session = Depends(get_db)):
    """Get library statistics."""
    return {
        "total_documentos": db.query(Documento).count(),
        "total_tipos": db.query(TipoDocumento).count(),
        "total_elementos_rbps": db.query(ElementoRBPS).count(),
        "total_relaciones": db.query(DocumentoRelacionado).count(),
        "documentos_por_tipo": [
            {
                "tipo": t.nombre,
                "cantidad": db.query(Documento).filter(Documento.tipo_id == t.id).count()
            }
            for t in db.query(TipoDocumento).all()
        ],
        "documentos_por_empresa": []
        # Temporarily disabled due to groupby complexity with nullable fields
    }


# ============ Semantic Search (Proyecto 2) ============

class BusquedaSemanticaSchema(BaseModel):
    consulta: str
    limite: int = 10
    umbral_vector: float = 0.2  # Minimum vector similarity
    peso_bm25: float = 0.4  # Weight for lexical search
    peso_vector: float = 0.6  # Weight for semantic search


class ResultadoBusquedaSchema(BaseModel):
    id_biblioteca: str
    titulo: str
    descripcion: Optional[str]
    puntuacion_hibrida: float
    tipo: str
    
    class Config:
        from_attributes = True


@app.post("/buscar-semantica/", response_model=list[ResultadoBusquedaSchema])
def buscar_semantica(busqueda: BusquedaSemanticaSchema, db: Session = Depends(get_db)):
    """
    Hybrid semantic + lexical search (Proyecto 2).
    
    Combines:
    - BM25 full-text search (lexical relevance)
    - Vector similarity search (semantic meaning)
    
    Returns documents ranked by combined score.
    """
    consulta = busqueda.consulta.strip()
    
    if not consulta:
        raise HTTPException(status_code=400, detail="Consulta vacía")
    
    # Perform hybrid search
    resultados = hybrid_search(
        db,
        query=consulta,
        limit=busqueda.limite,
        bm25_weight=busqueda.peso_bm25,
        vector_weight=busqueda.peso_vector,
        vector_threshold=busqueda.umbral_vector
    )
    
    # Format results
    return [
        ResultadoBusquedaSchema(
            id_biblioteca=doc.id_biblioteca,
            titulo=doc.titulo,
            descripcion=doc.descripcion,
            puntuacion_hibrida=score,
            tipo=doc.tipo.nombre
        )
        for doc, score in resultados
    ]


# ============ RAG / Asistente Generativo ============

@app.post("/asistente/preguntar", response_model=RespuestaAsistenteSchema)
def preguntar_asistente(
    pregunta_data: PreguntaAsistenteSchema,
    db: Session = Depends(get_db)
):
    """
    RAG endpoint: responde preguntas sobre seguridad de procesos.
    
    Flow:
    1. Busca documentos relevantes en la biblioteca
    2. Si hay resultados > umbral, construye contexto y consulta LLM
    3. Valida que todas las citas sean de documentos en el contexto
    4. Retorna respuesta + citas + documentos fuente + validación
    """
    pregunta = pregunta_data.pregunta.strip()
    umbral = pregunta_data.umbral_relevancia
    
    if not pregunta:
        raise HTTPException(status_code=400, detail="Pregunta vacía")
    
    # Buscar documentos relevantes (simple text search — idealmente sería embeddings/Proyecto 2)
    # MVP: retrieve sample docs for testing RAG quality, not retrieval quality
    docs = db.query(Documento).limit(10).all()
    
    # Check if results meet relevance threshold
    if not docs or len(docs) == 0:
        return RespuestaAsistenteSchema(
            respuesta="No tengo información suficiente en la biblioteca para responder esta pregunta.",
            citas=[],
            informacion_insuficiente=True,
            confianza=0.0,
            documentos_fuente=[],
            validacion_citas={"is_valid": True, "invalid_citations": [], "total_cited": 0}
        )
    
    # Format documents for LLM context
    docs_for_context = [
        {
            "id_biblioteca": d.id_biblioteca,
            "titulo": d.titulo,
            "tipo": d.tipo.nombre,
            "descripcion": d.descripcion or "N/A",
            "palabras_clave": d.palabras_clave or "N/A"
        }
        for d in docs
    ]
    
    # Build prompt and call LLM
    user_prompt = build_user_prompt(pregunta, docs_for_context)
    llm_response = call_llm(SYSTEM_PROMPT, user_prompt, temperature=0.2)
    
    if not llm_response:
        raise HTTPException(status_code=500, detail="Error al consultar el modelo LLM")
    
    # Validate citations
    available_ids = [d["id_biblioteca"] for d in docs_for_context]
    validation = validate_citations(llm_response, available_ids)
    
    # If citations are invalid, mark response as unreliable
    if not validation["is_valid"]:
        llm_response["informacion_insuficiente"] = True
        llm_response["confianza"] = 0.0
        llm_response["respuesta"] = "La respuesta generada contiene referencias a documentos que no fueron consultados. No puedo garantizar la confiabilidad."
    
    # Fetch full document data for response
    source_docs = db.query(Documento).filter(
        Documento.id_biblioteca.in_(available_ids)
    ).all()
    
    return RespuestaAsistenteSchema(
        respuesta=llm_response.get("respuesta", ""),
        citas=llm_response.get("citas", []),
        informacion_insuficiente=llm_response.get("informacion_insuficiente", False),
        confianza=llm_response.get("confianza", 0.0),
        documentos_fuente=source_docs,
        validacion_citas=validation
    )


# ============ Web UI ============

@app.get("/app")
def serve_ui():
    """Serve the web UI for the RAG assistant."""
    ui_path = os.path.join(os.path.dirname(__file__), "ui.html")
    return FileResponse(ui_path, media_type="text/html")


# ============ Health Check ============

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
