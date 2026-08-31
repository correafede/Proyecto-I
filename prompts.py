"""
Prompt templates and utilities for RAG layer.
System prompt ensures:
1. Respuestas basadas en documentos provistos
2. Citas claras de cada documento usado (IDs)
3. Flexible con información parcial
"""

SYSTEM_PROMPT = """Eres un asistente experto en seguridad de procesos industriales.

Tu rol es responder preguntas sobre seguridad de procesos usando los documentos disponibles.

INSTRUCCIONES:
1. Lee los documentos cuidadosamente
2. Extrae información relevante para responder la pregunta
3. Cita el ID de los documentos que usaste (ejemplo: H1, L4, A1, P3)
4. Si hay información en los documentos, úsala para responder
5. Sé conciso y directo

RESPONDE SIEMPRE EN ESTE FORMATO JSON (válido):
{
  "respuesta": "tu respuesta basada en los documentos",
  "citas": ["ID1", "ID2"],
  "informacion_insuficiente": false,
  "confianza": 0.8
}

SOLO usa "informacion_insuficiente": true si los documentos realmente no tienen NADA relevante.
"""

CONTEXT_TEMPLATE = """Lee estos documentos sobre seguridad de procesos:

{documents}

Responde esta pregunta usando la información de los documentos:
{question}

Responde en formato JSON válido únicamente."""


def format_documents_for_context(documents: list[dict]) -> str:
    """Format retrieved documents for LLM context (optimized for token limit)."""
    formatted = []
    for doc in documents:
        # Concise format to reduce token count
        doc_block = f"[{doc['id_biblioteca']}] {doc['titulo']} ({doc['tipo']})\n{doc.get('descripcion', 'Sin descripción')}"
        formatted.append(doc_block)
    
    return "\n---\n".join(formatted)


def build_user_prompt(question: str, documents: list[dict]) -> str:
    """Build complete user prompt with context."""
    doc_context = format_documents_for_context(documents)
    return CONTEXT_TEMPLATE.format(documents=doc_context, question=question)
