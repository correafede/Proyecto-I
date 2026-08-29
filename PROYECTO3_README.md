# Proyecto 3 — Capa Generativa (RAG)

Asistente que responde preguntas sobre seguridad de procesos usando RAG (Retrieval-Augmented Generation) con verificación de citas.

## Arquitectura

**3 capas:**
1. **Retrieval**: Búsqueda de documentos relevantes
2. **Generación**: LLM genera respuesta con prompts específicos
3. **Verificación**: Valida que todas las citas sean de documentos en el contexto

## Stack

- **LLM Provider**: Groq (Llama 3.3 70B)
- **LLM SDK**: OpenAI (compatible)
- **Prompt Design**: System prompt + structured JSON output
- **Citation Validation**: Deterministic check (no extra LLM calls)

## Setup

### 1. Obtener API Key de Groq

```bash
# Ir a https://console.groq.com/keys
# Crear una API key gratuita (sin tarjeta de crédito)
# Copiar la key
```

### 2. Configurar .env

```bash
# .env (gitignore, no commitar)
GROQ_API_KEY=gsk_tu_clave_aqui
```

### 3. Buildear y ejecutar

```bash
docker-compose up -d --build

# Esperar ~15 segundos
```

## Endpoint RAG

### POST `/asistente/preguntar`

**Request:**
```json
{
  "pregunta": "¿Qué pasa si se pierde el agua de enfriamiento?",
  "umbral_relevancia": 0.3
}
```

**Response:**
```json
{
  "respuesta": "Si se pierde el agua de enfriamiento del condensador...",
  "citas": ["H4", "L4"],
  "informacion_insuficiente": false,
  "confianza": 0.95,
  "documentos_fuente": [
    {
      "id_biblioteca": "H4",
      "titulo": "Estudio HAZOP – Condensador...",
      "tipo": "HAZOP",
      "descripcion": "...",
      "grupo_origen": "HAZOP (agrupado)"
    }
  ],
  "validacion_citas": {
    "is_valid": true,
    "invalid_citations": [],
    "total_cited": 2,
    "total_available": 5
  }
}
```

## Diseño del Prompt

### System Prompt
- Responder SOLO con info de documentos provistos
- Citar IDs explícitamente (H1, L4, A1, etc.)
- Declinar si no hay información suficiente
- Salida en JSON estructurado

### Validación de Citas
Post-processing determinístico:
1. Extraer `citas` del JSON del modelo
2. Verificar que cada ID esté en la lista de documentos pasados como contexto
3. Si hay IDs inválidos: marcar respuesta como no confiable

## Tests

### Ejecutar validation set completo

```bash
docker exec api-biblioteca python /app/test_validation_rag.py
```

**Espera:**
- 10 preguntas in-scope (debe encontrar respuestas)
- 3 preguntas out-of-scope (debe declinar)
- ~13 tests correctos = ✓

## Flujo Completo

```
Pregunta
  ↓
Búsqueda en biblioteca
  ↓
¿Resultados > umbral?
  ├─ NO → Responder "información insuficiente"
  └─ SÍ → Construir contexto
           ↓
        Llamar LLM con prompt
           ↓
        Validar citas
           ├─ Citas inválidas → Marcar no confiable
           └─ Citas válidas → Devolver respuesta
```

## Seguridad

- **API Key**: Solo en .env (gitignore)
- **No expone LLM internamente**: Todo vía Groq
- **No persiste conversación**: Stateless (V1)
- **Validación determinística**: Sin dependencia de otro LLM

## Limitaciones Conocidas (V1)

- ❌ No mantiene conversación (multi-turno)
- ❌ Búsqueda por texto simple (idealmente usaría embeddings del Proyecto 2)
- ❌ No reintenta si falla LLM
- ❌ No costo de tokens (solo para feedback)
- ⚠️ Groq free tier tiene rate limits

## Próximas Mejoras (V2)

- Integrar endpoint híbrido del Proyecto 2 (embeddings + BM25)
- Memoria de conversación con historial
- Verificador LLM-as-judge (para validad contenido, no solo citas)
- Reintento automático con diferentes parámetros
- Tracking de costo de tokens

## Preguntas de Prueba Rápidas

```bash
# In-scope (debe responder)
curl -X POST http://localhost:8000/asistente/preguntar \
  -H "Content-Type: application/json" \
  -d '{"pregunta":"¿Qué es HAZOP?"}'

# Out-of-scope (debe declinar)
curl -X POST http://localhost:8000/asistente/preguntar \
  -H "Content-Type: application/json" \
  -d '{"pregunta":"¿Cuál es la capital de Francia?"}'
```

## Swagger

- http://localhost:8000/docs
- Endpoint RAG bajo POST `/asistente/preguntar`

---

**Status**: ✓ MVP con RAG + Citation Validation
