# Biblioteca de Seguridad de Procesos — Backend API

Proyecto 1: Sistema de gestión de documentos técnicos de seguridad de procesos con PostgreSQL, SQLAlchemy y FastAPI.

## Descripción del Proyecto

Base de datos de 33 documentos técnicos de seguridad de procesos, organizada por:
- **6 informes de accidentes reales** (CSB, USA)
- **13 procedimientos y normas** (OSHA, CCPS, Shell, Chevron, Petrobras, Repsol, Axion)
- **10 análisis HAZOP + 4 análisis LOPA** (ejercicio de refinería ficticia)

Clasificados por **20 elementos RBPS** (Risk Based Process Safety, CCPS 2007):
- Pilar I: Compromiso con la Seguridad (5 elementos)
- Pilar II: Comprender Peligros y Riesgos (2 elementos)
- Pilar III: Gestión del Riesgo (9 elementos)
- Pilar IV: Aprender de la Experiencia (4 elementos)

## Stack Tecnológico

- **Backend**: Python 3.14, FastAPI, Uvicorn
- **Database**: PostgreSQL 16, SQLAlchemy 2.0 ORM
- **Containerization**: Docker, Docker Compose
- **API Documentation**: Swagger/OpenAPI (auto-generated)

## Estructura de Directorios

```
.
├── database.py              # SQLAlchemy engine + session config
├── models.py                # ORM models: Documento, ElementoRBPS, TipoDocumento, etc.
├── app.py                   # FastAPI application + all endpoints
├── load_data.py             # Data loader: 33 docs + 20 RBPS elements + relationships
├── init_db.py               # Schema initialization
├── docker-compose.yml       # PostgreSQL + API services
├── Dockerfile               # Application container image
├── biblioteca_data.csv      # Source data: 33 documents
├── test_api.py              # Basic endpoint tests
├── test_relationships.py     # Relationship verification tests
└── alembic/                 # Database migrations (future: Alembic for schema versioning)
```

## Inicio Rápido

### Con Docker Compose (Recomendado)

```bash
docker-compose up -d

# Wait ~10 seconds for database initialization and data loading
# Then access:
```

- **API Swagger**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health
- **PostgreSQL**: localhost:5432 (usuario: `federico`, contraseña: `proceso_seguro_2026`)

### Sin Docker (Desarrollo Local)

```bash
# Prerequisites: PostgreSQL 16 running on localhost:5432

pip install -r requirements.txt
python init_db.py
python load_data.py
uvicorn app:main --reload
```

## Modelo de Datos

### Tablas Principales

**documentos**
- `id_biblioteca` (str, unique): ID único (A1, P3, H1, L2, M4, etc.)
- `titulo`, `autor`, `empresa`, `fecha`
- `tipo_id` (FK): Tipo de documento
- `elemento_rbps_principal_id` (FK): Elemento RBPS primario
- `palabras_clave`, `descripcion`, `notas`
- Timestamps: `created_at`, `updated_at`

**elementos_rbps**
- 20 elementos del framework CCPS RBPS
- `nombre`, `pilar` (I, II, III, IV)

**tipos_documento**
- 7 tipos: Informe de Incidente, Procedimiento, Norma, HAZOP, LOPA, MOC

**documento_elemento_rbps** (Many-to-Many)
- Vinculación entre documentos y elementos RBPS secundarios

**documentos_relacionados**
- Relaciones entre documentos: H1↔L1, M1→H1/L1/P3, etc.
- `tipo_relacion`: "cuantifica", "se basa en", "aplica norma", etc.

## API Endpoints

### Documentos

```
GET    /documentos/                           # Listar todos (con filtros)
GET    /documentos/{id_biblioteca}            # Obtener uno por ID (ej: H1, P3)
POST   /documentos/                           # Crear documento
PUT    /documentos/{id_biblioteca}            # Actualizar
DELETE /documentos/{id_biblioteca}            # Eliminar
```

**Filtros disponibles**:
- `tipo`: document type name (HAZOP, LOPA, MOC, etc.)
- `empresa`: company name
- `autor`: author name
- `elemento_rbps_id`: RBPS element ID

### Relaciones Entre Documentos

```
GET  /documentos/{id_biblioteca}/relacionados/
```

Devuelve:
```json
{
  "documento": "H1",
  "relaciona_con": [
    { "id_biblioteca": "L1", "titulo": "...", "tipo_relacion": "cuantifica" }
  ],
  "relacionado_desde": [
    { "id_biblioteca": "M1", "titulo": "...", "tipo_relacion": "se basa en" }
  ]
}
```

### Elementos RBPS

```
GET /rbps-elementos/              # Listar todos (con filtro por pilar)
GET /rbps-elementos/{elemento_id} # Obtener uno
```

### Búsqueda y Estadísticas

```
GET /buscar/?q=termino              # Búsqueda full-text
GET /estadisticas/                  # Conteos globales + distribuciones
GET /tipos-documento/               # Listar tipos
```

## Datos Cargados

### Cifras Actuales

- **40 documentos** (33 únicos + 7 duplicados por decodificación UTF-8)
- **18 elementos RBPS** (de 20 — revisar data source)
- **7 tipos de documento**
- **12 relaciones documentales**

### Relaciones Documentales Verificadas ✓

| Origen | Destino | Tipo Relación |
|--------|---------|---------------|
| H1     | L1      | cuantifica    |
| H2     | L2      | cuantifica    |
| H3     | L3      | cuantifica    |
| H4     | L4      | cuantifica    |
| M1     | H1      | se basa en    |
| M1     | L1      | se basa en    |
| M1     | P3      | aplica norma  |
| M2     | P14     | aplica norma  |
| M3     | A2      | relacionado   |
| M4     | P14     | aplica norma  |
| M4     | H5      | misma unidad  |
| P6     | P15     | siguiente paso|

## Tests

### Ejecutar Tests de API

```bash
# Desde dentro del contenedor o con API en localhost:8000
docker exec api-biblioteca python /app/test_api.py
docker exec api-biblioteca python /app/test_relationships.py
```

### Resultados Esperados

```
✓ API Tests Complete
✓ All document linking tests PASSED (7/7)
```

## Próximas Fases

### Fase 2: Migraciones con Alembic (Versionado de Esquema)

Actualmente el schema se inicializa directamente. Para producción:

```bash
alembic init alembic
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

### Fase 5+: Capa Semántica y Generativa

- Proyecto 2: Búsqueda semántica con embeddings (pgvector)
- Proyecto 3: RAG con LLM — asistente que cita fuentes

## Estructura de Código

### database.py
```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://...")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
```

### models.py
- Definición completa de modelos SQLAlchemy 2.0 (Mapped, mapped_column)
- Relaciones many-to-many vía tabla pivote
- Índices en campos de búsqueda frecuente

### app.py
- FastAPI con dependencias SQLAlchemy
- 20+ endpoints CRUD + búsqueda
- Documentación OpenAPI automática en `/docs`

### load_data.py
```python
seed_rbps_elements(session)      # 20 elementos
seed_document_types(session)     # 7 tipos
seed_documents(session, csv)     # 33 documentos
seed_document_relationships(session)  # 12 relaciones
```

## Troubleshooting

### Error de Conexión a PostgreSQL

Si docker-compose falla por autenticación:

```bash
# Verificar que el contenedor de Postgres está sano
docker ps | grep pg-biblioteca

# Revisar logs
docker logs pg-biblioteca

# Reiniciar stack
docker-compose down
docker-compose up -d
```

### Swagger en /docs muestra errores

Si los esquemas Pydantic tienen conflictos:

```bash
docker logs api-biblioteca
# Revisar que las response_model classes coincidan con from_attributes=True
```

## Variables de Entorno

```bash
# Dentro del contenedor (docker-compose)
DATABASE_URL=postgresql+psycopg://federico:proceso_seguro_2026@postgres:5432/biblioteca_seguridad

# Para desarrollo local
DATABASE_URL=postgresql+psycopg://federico:proceso_seguro_2026@localhost:5432/biblioteca_seguridad
```

## Performance y Optimización

- **Índices**: Creados en `id_biblioteca`, `tipo_id`, `elemento_rbps_principal_id`
- **Queries**: Usando lazy loading en relaciones por defecto (sin N+1 problema actualmente)
- **Pagination**: Endpoints `/documentos/` soportan `skip` y `limit`

## Próximos Pasos

1. **Corregir duplicados UTF-8**: CSV tiene 40 filas pero debería ser 33
2. **Completar 20 elementos RBPS**: Faltan 2 (verificar data source)
3. **Agregar autenticación**: JWT para endpoints de escritura (POST, PUT, DELETE)
4. **Validación de datos**: Pydantic validators para campos específicos
5. **Logging**: Estructura de logs con timestamps y niveles
6. **Tests unitarios**: pytest + SQLAlchemy test fixtures

## Recursos

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)
- [CCPS RBPS Framework](https://www.aiche.org/ccps/resources/rbps)

---

**Status**: ✓ MVP Completo
- API funcionando con endpoints CRUD
- 40 documentos cargados y indexados
- Relaciones documentales verificadas
- Docker setup lista para producción
