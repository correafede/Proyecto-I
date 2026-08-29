# Quick Reference — Biblioteca de Seguridad de Procesos

## 🚀 Start Here (60 seconds)

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Docker
cd /path/to/proyecto
docker-compose up -d

# Open browser
http://localhost:8000/app
```

---

## 📋 Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/app` | GET | Web UI interface |
| `/docs` | GET | API documentation (Swagger) |
| `/health` | GET | Service health check |
| `/documentos` | GET | List all documents |
| `/documentos/{id}` | GET | Get document details |
| `/buscar-semantica/` | POST | Hybrid search |
| `/asistente/preguntar` | POST | RAG question answering |
| `/elementos-rbps/` | GET | RBPS framework elements |

---

## 🔧 Docker Commands

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f api

# Rebuild
docker-compose build --no-cache

# Run command in container
docker exec api-biblioteca python script.py

# Enter container
docker-compose exec api bash
```

---

## 🧪 Testing

```bash
# Run RAG validation
docker exec api-biblioteca python test_validation_rag.py

# Run API tests
docker exec api-biblioteca python test_api.py

# Check database
docker exec pg-biblioteca psql -U federico -d biblioteca_seguridad -c "SELECT COUNT(*) FROM documentos;"
```

---

## 📊 Example Requests

### List Documents
```bash
curl http://localhost:8000/documentos?limit=5
```

### Search Hybrid
```bash
curl -X POST http://localhost:8000/buscar-semantica/ \
  -H "Content-Type: application/json" \
  -d '{
    "consulta": "¿Qué es HAZOP?",
    "limite": 5,
    "peso_bm25": 0.4,
    "peso_vector": 0.6
  }'
```

### Ask RAG
```bash
curl -X POST http://localhost:8000/asistente/preguntar \
  -H "Content-Type: application/json" \
  -d '{
    "pregunta": "¿Cuáles son los elementos de RBPS?"
  }'
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" | Make sure `docker-compose up -d` completed (wait 30s) |
| "Invalid API key" | Use Ollama instead (it's now configured) |
| Ollama not found | Install from https://ollama.ai and run `ollama serve` |
| Embeddings not generating | Check Ollama is running; embeddings are optional for MVP |
| Nginx 502 error | `docker logs api-biblioteca` to check API status |
| Port already in use | Change port in docker-compose.yml or stop other services |

---

## 📁 Important Files

- `app.py` — Main API code
- `docker-compose.yml` — Development setup
- `docker-compose.prod.yml` — Production setup
- `ui.html` — Web interface
- `nginx.conf` — Reverse proxy
- `DEPLOYMENT.md` — Full deployment guide
- `.env` — Configuration (⚠️ keep secret!)

---

## 🔐 Security Reminders

⚠️ **NEVER**:
- Commit `.env` file to git
- Share API keys or passwords
- Deploy with DEBUG=true in production
- Expose database publicly

✅ **DO**:
- Use strong passwords (32+ chars)
- Rotate secrets regularly
- Enable SSL/TLS in production
- Restrict CORS to trusted origins
- Monitor logs for errors

---

## 📈 Production Checklist

- [ ] Environment `.env.prod` created
- [ ] SSL/TLS certificates obtained
- [ ] Database backups configured
- [ ] Rate limiting tested
- [ ] Health checks verified
- [ ] Logs monitored
- [ ] Scaling plan in place
- [ ] Disaster recovery tested

---

## 🆘 Support

**Check these first**:
1. Is Ollama running? `ollama serve` in terminal
2. Are containers running? `docker-compose ps`
3. Check API logs: `docker-compose logs api`
4. API health: `curl http://localhost:8000/health`

**Documentation**:
- Full guide: `DEPLOYMENT.md`
- Architecture: `PROJECT_COMPLETE.md`
- API docs: http://localhost:8000/docs

---

**Last Updated**: 2026-08-28  
**Version**: 1.0
