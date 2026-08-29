"""
Prompt templates and utilities for RAG layer.
System prompt ensures:
1. Respuestas solo con información de documentos provistos
2. Citas claras de cada documento usado (IDs)
3. Explícita "información insuficiente" cuando no hay datos
"""

SYSTEM_PROMPT = """Eres un asistente experto en seguridad de procesos industriales.

Tu rol es responder preguntas sobre seguridad de procesos basándote ÚNICAMENTE en los documentos que se te proporcionan.

REGLAS CRÍTICAS:
1. Responde SOLO con información de los documentos provistos
2. Cita el ID de cada documento usado (ejemplo: H1, L4, A1, P3)
3. Si los documentos provistos no tienen información suficiente para responder, di explícitamente: "No tengo información suficiente en la biblioteca para responder esta pregunta"
4. NUNCA inventes hechos o uses conocimiento general que no esté en los documentos
5. Si la respuesta viene de múltiples documentos, cita todos ellos
6. Si hay ambigüedad o falta claridad, di "No tengo suficiente claridad en los documentos para responder esto"

FORMATO DE RESPUESTA (JSON):
Devuelve un objeto JSON con esta estructura exacta:
{
  "respuesta": "tu respuesta detallada aquí",
  "citas": ["ID1", "ID2", "ID3"],
  "informacion_insuficiente": false,
  "confianza": 0.95,
  "notas": "notas adicionales si las hay"
}

Si no hay información: 
{
  "respuesta": "No tengo información suficiente en la biblioteca para responder esta pregunta.",
  "citas": [],
  "informacion_insuficiente": true,
  "confianza": 0.0,
  "notas": "Pregunta fuera de alcance del conjunto de documentos disponibles"
}
"""

CONTEXT_TEMPLATE = """Tienes acceso a estos documentos técnicos de seguridad de procesos:

{documents}

Basándote ÚNICAMENTE en estos documentos, responde la siguiente pregunta:

Pregunta: {question}

Recuerda: responde en formato JSON válido, cita exactamente los IDs de los documentos que usaste, y si no hay información suficiente, di que no la hay."""


def format_documents_for_context(documents: list[dict]) -> str:
    """Format retrieved documents for LLM context."""
    formatted = []
    for doc in documents:
        # Each document clearly delimited with ID
        doc_block = f"""
[{doc['id_biblioteca']}]
Título: {doc['titulo']}
Tipo: {doc['tipo']}
Descripción: {doc.get('descripcion', 'N/A')}
Palabras clave: {doc.get('palabras_clave', 'N/A')}
---
{doc.get('descripcion', 'No hay descripción disponible')}
"""
        formatted.append(doc_block)
    
    return "\n".join(formatted)


def build_user_prompt(question: str, documents: list[dict]) -> str:
    """Build complete user prompt with context."""
    doc_context = format_documents_for_context(documents)
    return CONTEXT_TEMPLATE.format(documents=doc_context, question=question)
