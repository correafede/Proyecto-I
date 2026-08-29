# Biblioteca de Seguridad de Procesos — Proyectos 1, 2, 3 Completos

## Resumen Ejecutivo

Sistema completo de gestión y búsqueda inteligente de documentos técnicos de seguridad de procesos:

- **Proyecto 1** ✓: Backend CRUD + base de datos normalizada (33 documentos, 20 elementos RBPS)
- **Proyecto 2** (En desarrollo): Búsqueda semántica con embeddings (pgvector + Llama)
- **Proyecto 3** ✓: Asistente RAG con citas verificables (Groq LLM + Citation Checking)

## Proyectos Completados

### Proyecto 1: Backend + Base de Datos

**Ubicación**: `./` (archivos principales)

**Entregables:**
- ✓ PostgreSQL 16 con 5 tablas normalizadas
- ✓ SQLAlchemy 2.0 ORM con relaciones many-to-many
- ✓ FastAPI con 20+ endpoints CRUD
- ✓ 40 documentos cargados + 18 elementos RBPS + 12 relaciones
- ✓ Docker Compose setup

**Archivos:**
```
database.py         # SQLAlchemy engine + session
models.py           # ORM: Documento, ElementoRBPS, TipoDocumento, etc.
app.py              # FastAPI endpoints
load_data.py        # Cargador de datos
init_db.py          # Inicializador de esquema
biblioteca_data.csv # Datos: 33 documentos
docker-compose.yml  # Servicios
Dockerfile          # API container
```

**Verificación:**
```bash
docker exec api-biblioteca python /app/test_api.py
docker exec api-biblioteca python /app/test_relationships.py
# ✓ API Tests Complete
# ✓ All document linking tests PASSED (7/7)
```

**Endpoints Principales:**
```
GET    /documentos/                        # Listar con filtros
GET    /documentos/{id}                    # Obtener por ID
GET    /documentos/{id}/relacionados/      # Ver relaciones (H1↔L1, etc.)
GET    /rbps-elementos/                    # Listar 20 elementos RBPS
GET    /buscar/?q=termino                  # Búsqueda full-text
GET    /estadisticas/                      # Conteos y distribuciones
```

---

### Proyecto 3: Capa Generativa (RAG)

**Ubicación**: `./PROYECTO3_README.md` (documentación completa)

**Entregables:**
- ✓ Prompt system para respuestas ancladas
- ✓ Integración Groq (Llama 3.3 70B)
- ✓ Endpoint POST `/asistente/preguntar`
- ✓ Validación de citas determinística
- ✓ Test set con 13 preguntas (10 in-scope + 3 out-of-scope)
- ✓ Manejo de secretos (.env / .gitignore)

**Archivos:**
```
prompts.py              # System prompt + templates
llm_service.py          # Groq integration + citation validation
app.py (actualizado)    # Nuevo endpoint POST /asistente/preguntar
test_validation_rag.py  # Validation set (13 preguntas)
.env.example            # Template para API key
.env                    # Real (gitignore)
.gitignore              # Secretos protegidos
PROYECTO3_README.md     # Documentación completa
```

**Flujo RAG:**
```
Pregunta
  ↓
Búsqueda en biblioteca (Proyecto 1)
  ↓
¿Hay documentos relevantes?
  ├─ NO → "No tengo información suficiente"
  └─ SÍ → Construir contexto + llamar LLM
           ↓
          Validar citas (¿están en contexto?)
           ├─ Inválidas → Marcar no confiable
           └─ Válidas → Devolver respuesta + documentos fuente
```

**Setup:**
```bash
# 1. Obtener API key de Groq (gratis, sin tarjeta)
# https://console.groq.com/keys

# 2. Configurar .env
echo "GROQ_API_KEY=gsk_tu_clave_aqui" > .env

# 3. Buildear
docker-compose up -d --build

# 4. Esperar 15s y testear
docker exec api-biblioteca python /app/test_validation_rag.py
```

**Ejemplo de Uso:**
```bash
curl -X POST http://localhost:8000/asistente/preguntar \
  -H "Content-Type: application/json" \
  -d '{
    "pregunta": "¿Qué pasa si se pierde el agua de enfriamiento?",
    "umbral_relevancia": 0.3
  }'
```

**Response:**
```json
{
  "respuesta": "Si se pierde el agua de enfriamiento del condensador...",
  "citas": ["H4", "L4"],
  "informacion_insuficiente": false,
  "confianza": 0.95,
  "validacion_citas": {
    "is_valid": true,
    "invalid_citations": [],
    "total_cited": 2
  },
  "documentos_fuente": [...]
}
```

---

## Proyecto 2: Capa Semántica (Pendiente)

**Descripción:**
Búsqueda semántica híbrida (embeddings + BM25) usando pgvector y modelos de embeddings.

**Interfaz esperada:**
```
POST /buscar-semantica/
  Request: { "query": string, "top_k": int }
  Response: [{ id_biblioteca, titulo, score, embedding_score, bm25_score }, ...]
```

**Uso en Proyecto 3:**
En lugar de búsqueda por texto simple, el endpoint RAG llamaría a este endpoint para recuperar documentos relevantes por significado.

---

## Arquitectura Completa (3 Capas)

```
┌─────────────────────────────────────┐
│   USUARIO (Web/API/Chatbot)         │
└──────────────┬──────────────────────┘
               │
        POST /asistente/preguntar
               ↓
    ┌──────────────────────────┐
    │   Proyecto 3: Generativo │
    │   (RAG + Citations)      │
    │   - Prompt system        │
    │   - LLM (Groq)           │
    │   - Citation validation  │
    └──────────┬───────────────┘
               │
        POST /buscar-semantica/  ← Proyecto 2 (TODO)
               ↓
    ┌──────────────────────────┐
    │  Proyecto 2: Semántica   │
    │  (Embeddings + BM25)     │
    │  - pgvector              │
    │  - Embeddings            │
    │  - Hybrid search         │
    └──────────┬───────────────┘
               │
        GET /documentos/ + relaciones
               ↓
    ┌──────────────────────────┐
    │  Proyecto 1: Backend     │
    │  (CRUD + DB)             │
    │  - FastAPI               │
    │  - PostgreSQL            │
    │  - SQLAlchemy ORM        │
    │  - 40 documentos         │
    └──────────────────────────┘
```

---

## Datos Cargados

### 40 Documentos (33 únicos)

| Grupo | Cantidad | Ejemplos |
|-------|----------|----------|
| Accidentes CSB | 6 | A1-A6 (Valero, Chevron, Tesoro, ExxonMobil, PES, Husky) |
| Procedimientos/Normas | 13 | P1-P16 (OSHA, CCPS, Shell, Chevron, Petrobras, Repsol, Axion) |
| HAZOP | 10 | H1-H10 (refinería ficticia) |
| LOPA | 4 | L1-L4 (cuantificación de riesgos) |
| MOC | 4 | M1-M4 (gestión del cambio) |

### 20 Elementos RBPS

**Pilar I: Compromiso** (5)
- Cultura, Cumplimiento, Competencia, Participación, Partes Interesadas

**Pilar II: Comprender** (2)
- Conocimiento del Proceso, HIRA

**Pilar III: Gestión del Riesgo** (9)
- Procedimientos, Integridad Mecánica, MOC, Emergencias, Trabajo Seguro, Preparación, Entrenamiento, Auditorías, Métricas

**Pilar IV: Aprender** (2)
- Investigación de Incidentes, Revisión de Gestión

### 12 Relaciones Documentales

- H1 ↔ L1: HAZOP cuantificado por LOPA
- H2 ↔ L2: Mismo
- H3 ↔ L3: Mismo
- H4 ↔ L4: Mismo
- M1 → H1, L1, P3: MOC implementa recomendaciones
- M2 → P14: MOC aplica política ExxonMobil
- M3 → A2: RBI conecta con accidente (tema)
- M4 → P14, H5: MOC organizacional + contexto
- P6 → P15: SCOR continúa workflow

---

## Stack Tecnológico Completo

### Backend
- **Python 3.14**
- **FastAPI** (web framework)
- **SQLAlchemy 2.0** (ORM)
- **Pydantic** (validation)

### Database
- **PostgreSQL 16** (relacional)
- **pgvector** (preparado para embeddings)

### LLM & IA
- **Groq** (LLM provider - free tier)
- **Llama 3.3 70B** (modelo)
- **OpenAI SDK** (compatible)

### DevOps
- **Docker** (containerización)
- **Docker Compose** (orquestación)
- **Environment variables** (.env)

### Testing
- **Custom test scripts** (Python)
- **Validación end-to-end**

---

## Cómo Ejecutar

### Inicio Rápido

```bash
# 1. Clonar/descargar
cd ~/biblioteca-seguridad

# 2. Configurar secreto (Proyecto 3)
echo "GROQ_API_KEY=gsk_tu_api_key" > .env

# 3. Levantar stack completo
docker-compose up -d

# 4. Esperar 15-20 segundos

# 5. Verificar
curl http://localhost:8000/health
# {"status":"ok"}

# 6. Acceder a Swagger
# http://localhost:8000/docs
```

### Tests

```bash
# Proyecto 1: CRUD endpoints
docker exec api-biblioteca python /app/test_api.py

# Proyecto 1: Document relationships
docker exec api-biblioteca python /app/test_relationships.py

# Proyecto 3: RAG validation
docker exec api-biblioteca python /app/test_validation_rag.py
```

---

## Decisiones Clave (ADR)

### Proyecto 1
- ✓ PostgreSQL nativo (en lugar de Supabase)
- ✓ SQLAlchemy 2.0 (sintaxis moderna con Mapped)
- ✓ FastAPI (async + OpenAPI automático)
- ✓ Docker Compose (dev + prod-like)

### Proyecto 3
- ✓ **LLM Provider**: Groq (gratis, sin fricción, sin hardware dependency)
- ✓ **Prompt**: System + structured JSON output
- ✓ **Citation Validation**: Determinístico (sin extra LLM)
- ✓ **Architecture**: Stateless (V1), single-turn QA
- ✓ **Secrets**: .env + .gitignore (nunca commitear API keys)

---

## Limitaciones Conocidas

### Proyecto 1
- ❌ No hay autenticación (TODO: JWT para POST/PUT/DELETE)
- ❌ No hay paginación de keywords

### Proyecto 3
- ❌ No mantiene conversación (multi-turno)
- ❌ Búsqueda por texto simple (idealmente usaría Proyecto 2)
- ❌ Groq free tier: rate limits ~30 req/min
- ❌ Sin reintento automático si falla LLM

### Proyecto 2 (TODO)
- ❌ No implementado aún
- ❌ Necesita embeddings model (Llama o similar)
- ❌ Necesita pgvector extensión activa en PostgreSQL

---

## Próximas Mejoras

### V1.1 (Corto plazo)
- Integrar búsqueda del Proyecto 2
- Agregar autenticación JWT
- Reintento automático si falla LLM
- Cache de respuestas frecuentes

### V2 (Mediano plazo)
- Conversación multi-turno (memory)
- Verificador LLM-as-judge
- Tracking de costo de tokens
- UI de chat (Streamlit o HTML+JS)

### V3 (Largo plazo)
- RAG offline (sin Groq)
- Fine-tuning de modelo local
- Exportar a diferentes formatos
- Analytics dashboard

---

## Contribuyentes

- **Proyecto 1**: Backend + Base de Datos
- **Proyecto 2**: Búsqueda Semántica (en desarrollo)
- **Proyecto 3**: Capa Generativa con RAG

---

## License

Sin especificar (proyecto educativo)

---

## Contacto / Soporte

Para preguntas sobre la arquitectura o la implementación, revisar:
1. `README.md` (Proyecto 1)
2. `PROYECTO3_README.md` (Proyecto 3)
3. Docstrings en código (todo modulo tiene docstring)

---

**Status Overall**: ✓ MVP Completo (Proyectos 1 + 3), Proyecto 2 Pendiente
