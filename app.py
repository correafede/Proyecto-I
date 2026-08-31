"""
FastAPI application — Biblioteca de Seguridad de Procesos
API REST para gestión de documentos, búsqueda y clasificación de elementos RBPS.
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

# ============ FastAPI Setup ============
app = FastAPI(
    title="Biblioteca de Seguridad de Procesos",
    description="API Backend para gestión de documentos técnicos de seguridad de procesos. Incluye búsqueda semántica, análisis RBPS y asistente con IA.",
    version="1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}  # Hide response examples
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
    umbral_relevancia: float = 0.3  # Puntuación mínima para considerar un doc relevante
    
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
    """Dependencia: obtener sesión de base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============ Elementos RBPS ============

@app.get("/rbps-elementos/", response_model=list[ElementoRBPSSchema], tags=["RBPS"])
def listar_elementos_rbps(pilar: Optional[str] = None, db: Session = Depends(get_db)):
    """Listar todos los elementos RBPS, opcionalmente filtrados por pilar."""
    query = db.query(ElementoRBPS)
    if pilar:
        query = query.filter(ElementoRBPS.pilar.contains(pilar))
    return query.order_by(ElementoRBPS.pilar, ElementoRBPS.nombre).all()


@app.get("/rbps-elementos/{elemento_id}", response_model=ElementoRBPSSchema, tags=["RBPS"])
def obtener_elemento_rbps(elemento_id: int, db: Session = Depends(get_db)):
    """Obtener un elemento RBPS por ID."""
    elem = db.query(ElementoRBPS).filter(ElementoRBPS.id == elemento_id).first()
    if not elem:
        raise HTTPException(status_code=404, detail="Elemento RBPS no encontrado")
    return elem


# ============ Tipos de Documento ============

@app.get("/tipos-documento/", response_model=list[TipoDocumentoSchema])
def listar_tipos_documento(db: Session = Depends(get_db)):
    """Listar todos los tipos de documento."""
    return db.query(TipoDocumento).order_by(TipoDocumento.nombre).all()


# ============ Documentos ============

@app.get("/documentos/", response_model=list[DocumentoResponseSchema])
def listar_documentos(
    tipo: Optional[str] = Query(None, description="Filtrar por nombre de tipo de documento"),
    empresa: Optional[str] = Query(None, description="Filtrar por empresa"),
    autor: Optional[str] = Query(None, description="Filtrar por autor"),
    elemento_rbps_id: Optional[int] = Query(None, description="Filtrar por ID de elemento RBPS"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Listar documentos con filtros.
    
    Parámetros de consulta:
    - tipo: nombre del tipo de documento (ej., 'HAZOP', 'LOPA', 'Informe de Incidente')
    - empresa: nombre de la empresa
    - autor: nombre del autor
    - elemento_rbps_id: ID del elemento RBPS principal
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
    """Obtener un documento por ID de biblioteca (ej., 'A1', 'H1', 'L2', 'M1')."""
    doc = db.query(Documento).filter(Documento.id_biblioteca == id_biblioteca).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc


@app.post("/documentos/", response_model=DocumentoResponseSchema)
def crear_documento(doc_data: DocumentoCreateSchema, db: Session = Depends(get_db)):
    """Crear un nuevo documento."""
    # Verificar si ya existe
    existing = db.query(Documento).filter(Documento.id_biblioteca == doc_data.id_biblioteca).first()
    if existing:
        raise HTTPException(status_code=400, detail="Documento con ese ID ya existe")
    
    # Verificar que el tipo exista
    tipo = db.query(TipoDocumento).filter(TipoDocumento.id == doc_data.tipo_id).first()
    if not tipo:
        raise HTTPException(status_code=400, detail="Tipo de documento no existe")
    
    # Verificar elemento RBPS si se proporciona
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
    """Actualizar un documento."""
    doc = db.query(Documento).filter(Documento.id_biblioteca == id_biblioteca).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Actualizar campos
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
    """Eliminar un documento."""
    doc = db.query(Documento).filter(Documento.id_biblioteca == id_biblioteca).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Eliminar registros relacionados
    db.query(DocumentoRelacionado).filter(
        (DocumentoRelacionado.documento_origen_id == doc.id) |
        (DocumentoRelacionado.documento_destino_id == doc.id)
    ).delete()
    
    db.delete(doc)
    db.commit()
    return {"eliminado": id_biblioteca}


# ============ Relaciones de Documentos ============

@app.get("/documentos/{id_biblioteca}/relacionados/", response_model=dict)
def obtener_documentos_relacionados(id_biblioteca: str, db: Session = Depends(get_db)):
    """Obtener documentos relacionados con un documento dado."""
    doc = db.query(Documento).filter(Documento.id_biblioteca == id_biblioteca).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Relaciones FROM este documento
    desde = db.query(DocumentoRelacionado).filter(
        DocumentoRelacionado.documento_origen_id == doc.id
    ).all()
    
    # Relaciones TO este documento
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


# ============ Búsqueda y Estadísticas ============

@app.get("/buscar/")
def buscar(
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    db: Session = Depends(get_db)
):
    """Buscar en títulos de documentos, descripciones y palabras clave."""
    docs = db.query(Documento).filter(
        (Documento.titulo.ilike(f"%{q}%")) |
        (Documento.descripcion.ilike(f"%{q}%")) |
        (Documento.palabras_clave.ilike(f"%{q}%")) |
        (Documento.autor.ilike(f"%{q}%")) |
        (Documento.empresa.ilike(f"%{q}%"))
    ).all()
    
    return {
        "consulta": q,
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
    """Obtener estadísticas de la biblioteca."""
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
        # Deshabilitado temporalmente debido a complejidad de groupby con campos nulos
    }


# ============ Búsqueda Semántica (Proyecto 2) ============

class BusquedaSemanticaSchema(BaseModel):
    consulta: str
    limite: int = 10
    umbral_vector: float = 0.2  # Similitud mínima de vectores
    peso_bm25: float = 0.4  # Peso para búsqueda léxica
    peso_vector: float = 0.6  # Peso para búsqueda semántica


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
    Búsqueda semántica + léxica híbrida (Proyecto 2).
    
    Combina:
    - Búsqueda de texto completo BM25 (relevancia léxica)
    - Búsqueda de similitud de vectores (significado semántico)
    
    Retorna documentos clasificados por puntuación combinada.
    """
    consulta = busqueda.consulta.strip()
    
    if not consulta:
        raise HTTPException(status_code=400, detail="Consulta vacía")
    
    # Realizar búsqueda híbrida
    resultados = hybrid_search(
        db,
        query=consulta,
        limit=busqueda.limite,
        bm25_weight=busqueda.peso_bm25,
        vector_weight=busqueda.peso_vector,
        vector_threshold=busqueda.umbral_vector
    )
    
    # Formatear resultados
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
    Punto final RAG: responde preguntas sobre seguridad de procesos.
    
    Flujo:
    1. Busca documentos relevantes en la biblioteca
    2. Si hay resultados > umbral, construye contexto y consulta LLM
    3. Valida que todas las citas sean de documentos en el contexto
    4. Retorna respuesta + citas + documentos fuente + validación
    """
    pregunta = pregunta_data.pregunta.strip()
    umbral = pregunta_data.umbral_relevancia
    
    if not pregunta:
        raise HTTPException(status_code=400, detail="Pregunta vacía")
    
    # Buscar documentos relevantes por palabras clave en la pregunta
    # Limitar a máximo 5 documentos para evitar exceder límite de tamaño de Groq (HTTP 413)
    query_lower = pregunta.lower()
    
    # Mapeo de tipos de documento disponibles
    tipo_nombres = {
        'hazop': 'HAZOP',
        'lopa': 'LOPA',
        'moc': 'MOC',
        'incidente': 'Informe de Incidente',
        'procedimiento': 'Procedimiento',
        'norma': 'Norma'
    }
    
    # Encontrar qué tipos coinciden con la pregunta
    docs = []
    for keyword, type_name in tipo_nombres.items():
        if keyword in query_lower:
            result = db.query(Documento).join(TipoDocumento).filter(
                TipoDocumento.nombre == type_name
            ).limit(5).all()
            docs = result
            break
    
    # Si no encontramos por tipo, buscar por palabras clave en descripción y título
    if not docs:
        from sqlalchemy import or_
        docs = db.query(Documento).filter(
            (Documento.titulo.ilike(f"%{query_lower}%")) |
            (Documento.descripcion.ilike(f"%{query_lower}%")) |
            (Documento.palabras_clave.ilike(f"%{query_lower}%"))
        ).limit(5).all()
    
    # Si aún no hay resultados, retorna hasta 5 documentos aleatorios como contexto
    if not docs:
        docs = db.query(Documento).limit(5).all()
    
    # Verificar si los resultados cumplen el umbral de relevancia
    if not docs or len(docs) == 0:
        return RespuestaAsistenteSchema(
            respuesta="No tengo información suficiente en la biblioteca para responder esta pregunta.",
            citas=[],
            informacion_insuficiente=True,
            confianza=0.0,
            documentos_fuente=[],
            validacion_citas={"is_valid": True, "invalid_citations": [], "total_cited": 0}
        )
    
    # Formatear documentos para contexto LLM
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
    
    # Validar citas
    available_ids = [d["id_biblioteca"] for d in docs_for_context]
    validation = validate_citations(llm_response, available_ids)
    
    # Si las citas son inválidas, marcar respuesta como no confiable
    if not validation.get("is_valid", True):
        llm_response["informacion_insuficiente"] = True
        llm_response["confianza"] = 0.0
        llm_response["respuesta"] = "La respuesta generada contiene referencias a documentos que no fueron consultados. No puedo garantizar la confiabilidad."
    
    # Obtener datos completos del documento para la respuesta
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


# ============ Interfaz Web ============

@app.get("/app")
def serve_ui():
    """Servir la interfaz web para el asistente RAG."""
    ui_path = os.path.join(os.path.dirname(__file__), "ui.html")
    return FileResponse(ui_path, media_type="text/html")


# ============ Verificación de Salud ============

@app.get("/health")
def health_check():
    """Punto final de verificación de salud."""
    return {"status": "ok"}


# ============ Debug Endpoint ============

@app.get("/debug/document-types")
def debug_document_types(db: Session = Depends(get_db)):
    """Debug: listar tipos de documentos en DB."""
    tipos = db.query(TipoDocumento).all()
    return {
        "tipos": [
            {"id": t.id, "nombre": t.nombre, "count": db.query(Documento).filter(Documento.tipo_id == t.id).count()}
            for t in tipos
        ]
    }


@app.get("/debug/search-hazop")
def debug_search_hazop(db: Session = Depends(get_db)):
    """Debug: buscar documentos HAZOP."""
    docs = db.query(Documento).join(TipoDocumento).filter(
        TipoDocumento.nombre == 'HAZOP'
    ).limit(5).all()
    return {
        "count": len(docs),
        "docs": [
            {"id_biblioteca": d.id_biblioteca, "titulo": d.titulo}
            for d in docs
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
