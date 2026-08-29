# Deployment Guide — Biblioteca de Seguridad de Procesos

## Overview

This document covers deploying the Biblioteca de Seguridad de Procesos system:
- **Proyecto 1**: FastAPI backend with PostgreSQL + pgvector
- **Proyecto 2**: Hybrid semantic search (BM25 + vector similarity)
- **Proyecto 3**: RAG layer with Ollama LLM inference
- **UI/UX**: Web interface + Swagger documentation

---

## Local Development Setup

### Prerequisites
- Docker Desktop (includes Docker Compose)
- Ollama (for local LLM inference)
- Python 3.14+ (optional, for local development)

### Quick Start

```bash
# 1. Install Ollama from https://ollama.ai
# 2. Start Ollama in a separate terminal
ollama serve

# 3. In another terminal, clone/navigate to project
cd /path/to/biblioteca

# 4. Start containers (development mode)
docker-compose up -d

# 5. Open browser
http://localhost:8000/app
```

### Environment Variables (Development)

Create `.env` file:
```bash
# API Configuration
ENVIRONMENT=development
API_PORT=8000

# Database
DB_USER=federico
DB_PASSWORD=proceso_seguro_2026
DB_NAME=biblioteca_seguridad
DB_PORT=5432

# Ollama (local inference)
OLLAMA_HOST=host.docker.internal:11434
OLLAMA_MODEL=llama2
```

### Testing

```bash
# Run API tests
docker exec api-biblioteca python test_api.py
docker exec api-biblioteca python test_relationships.py

# Run RAG validation
docker exec api-biblioteca python test_validation_rag.py

# Check health
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Swagger UI
```

---

## Production Deployment

### Architecture

```
┌─────────────┐
│   Clients   │
└──────┬──────┘
       │ HTTPS
       ▼
┌──────────────────────────────────────┐
│  Nginx (Reverse Proxy + LB)          │
│  - Rate limiting                     │
│  - Gzip compression                  │
│  - SSL/TLS termination               │
└─────────────┬──────────────────────────┘
              │
       ┌──────┴──────┐
       ▼             ▼
   ┌─────────┐   ┌─────────┐
   │ API 1   │   │ API 2   │  (Scaled instances)
   └────┬────┘   └────┬────┘
        │             │
        └──────┬──────┘
               ▼
        ┌─────────────────┐
        │  PostgreSQL     │
        │  + pgvector     │
        │  (persistent)   │
        └─────────────────┘
```

### Option 1: Docker Compose (Single Host)

Ideal for small deployments, development, or single-server production.

```bash
# 1. Create production environment file
cat > .env.prod << EOF
ENVIRONMENT=production
API_PORT=8000
DB_USER=prod_user
DB_PASSWORD=$(openssl rand -base64 32)
DB_NAME=biblioteca_seguridad
OLLAMA_HOST=ollama:11434  # Or remote Ollama server
EOF

# 2. Start with production compose file
docker-compose -f docker-compose.prod.yml up -d

# 3. Verify health
curl http://localhost/health
curl http://localhost/app
```

**Features:**
- ✓ Nginx reverse proxy + rate limiting
- ✓ PostgreSQL with data persistence
- ✓ Health checks on all services
- ✓ Structured logging (JSON format)
- ✓ Container restart policies
- ✓ Resource limits (optional - add to compose file)

### Option 2: Kubernetes (Multi-Node / Cloud)

For high-availability enterprise deployments.

```bash
# 1. Create namespace
kubectl create namespace biblioteca

# 2. Create secrets
kubectl -n biblioteca create secret generic db-credentials \
  --from-literal=user=prod_user \
  --from-literal=password=$(openssl rand -base64 32)

# 3. Deploy (using Kubernetes manifests - see below)
kubectl apply -f k8s/

# 4. Check status
kubectl -n biblioteca get pods
kubectl -n biblioteca logs deployment/api-biblioteca
```

### Option 3: Cloud Platforms

#### AWS ECS/Fargate

```bash
# 1. Push images to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ECR_URI>
docker tag default-api:latest <ECR_URI>/api:latest
docker push <ECR_URI>/api:latest

# 2. Create ECS task definition (references ECR images)
# 3. Deploy to Fargate cluster
# 4. RDS PostgreSQL for database (managed)
```

#### Google Cloud Run

```bash
# 1. Build and push to Artifact Registry
gcloud builds submit --tag gcr.io/<PROJECT>/api

# 2. Deploy
gcloud run deploy api-biblioteca \
  --image gcr.io/<PROJECT>/api \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --set-env-vars ENVIRONMENT=production,DATABASE_URL=...

# 3. Note: PostgreSQL via Cloud SQL (managed service)
```

#### Azure Container Instances / App Service

```bash
# 1. Push to Azure Container Registry
az acr build --registry <ACR_NAME> --image api:latest .

# 2. Deploy via Container Instances or App Service
az container create \
  --resource-group <RG> \
  --name api-biblioteca \
  --image <ACR_NAME>.azurecr.io/api:latest \
  --environment-variables ENVIRONMENT=production ...
```

---

## Production Configuration

### SSL/TLS Certificates

**Using Let's Encrypt (Free)**

```bash
# 1. Install certbot
apt-get install certbot python3-certbot-nginx

# 2. Generate certificate
certbot certonly --standalone -d yourdomain.com

# 3. Update nginx.conf with certificate paths:
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

# 4. Enable auto-renewal
certbot renew --dry-run
```

### Environment-Specific Settings

Create separate `.env` files:

**`.env.dev`** (Development)
```
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DB_ECHO=true  # Log all SQL queries
```

**`.env.staging`** (Staging/Testing)
```
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
DB_ECHO=false
```

**`.env.prod`** (Production)
```
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DB_ECHO=false
CORS_ORIGINS=["https://yourdomain.com"]
```

### Resource Limits

Add to `docker-compose.prod.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

---

## Monitoring & Logging

### Health Checks

All services have built-in health checks:

```bash
# API health
curl http://localhost:8000/health

# Database health
curl http://localhost:5432  # Or use pg_isready

# Nginx health
curl http://localhost/health
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Follow API logs
docker exec api-biblioteca tail -f /app/logs/app.log

# Nginx access logs
docker exec nginx-biblioteca tail -f /var/log/nginx/access.log
```

### Performance Monitoring

**Using Prometheus + Grafana (Optional)**

```bash
# Add monitoring stack to docker-compose.prod.yml
# See examples/ directory for configuration
```

---

## Database Backups & Persistence

### Manual Backup

```bash
# Backup PostgreSQL
docker exec pg-biblioteca pg_dump -U federico biblioteca_seguridad \
  > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker exec -i pg-biblioteca psql -U federico biblioteca_seguridad \
  < backup_20260828_120000.sql
```

### Automated Backups

```bash
# Create backup script (backup.sh)
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker exec pg-biblioteca pg_dump -U federico biblioteca_seguridad \
  | gzip > $BACKUP_DIR/backup_$TIMESTAMP.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

# Add to crontab (daily at 2 AM)
0 2 * * * /path/to/backup.sh
```

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect default_postgres_data

# Backup volume data
docker run --rm -v default_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_data.tar.gz -C /data .
```

---

## Security Best Practices

1. **Secrets Management**
   - Never commit `.env` files to git
   - Use Docker secrets or cloud provider KMS
   - Rotate credentials regularly

2. **Database Security**
   - Use strong passwords (minimum 32 characters)
   - Restrict PostgreSQL to internal network only
   - Enable SSL connections (`sslmode=require`)
   - Regular security updates

3. **API Security**
   - Enable CORS only for trusted origins
   - Implement API authentication (JWT/OAuth2)
   - Rate limiting (configured in nginx)
   - Input validation on all endpoints

4. **Container Security**
   - Use specific image versions (no `latest` tags in production)
   - Scan images for vulnerabilities (`docker scan`)
   - Run containers as non-root user
   - Use read-only filesystems where possible

5. **Network Security**
   - Use VPC/private networks
   - Firewall rules (allow only necessary ports)
   - WAF (Web Application Firewall) for DDoS protection
   - Disable public database access

---

## Scaling & Load Balancing

### Horizontal Scaling (Multiple API Instances)

```yaml
# docker-compose.prod.yml
services:
  api:
    deploy:
      replicas: 3  # Run 3 instances
  
  nginx:
    # Already configured with upstream load balancing
```

### Database Scaling

For PostgreSQL read replicas:
- Primary database (write): Internal only
- Read replicas: Optional for read-heavy workloads
- Use connection pooling (PgBouncer)

### Caching Layer (Redis - Optional)

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
```

---

## Troubleshooting

### Container Fails to Start

```bash
# Check logs
docker-compose logs api

# Verify environment variables
docker-compose config | grep -A20 "api:"

# Test database connection
docker exec api-biblioteca python -c "from database import engine; engine.connect()"
```

### High Memory Usage

```bash
# Check container stats
docker stats

# Limit memory and restart
docker-compose down
# Edit docker-compose.yml to add memory limits
docker-compose up -d
```

### Slow Queries

```bash
# Enable query logging in PostgreSQL
# Edit docker-compose.yml:
command: postgres -c log_statement=all -c log_duration=on

# Check slow queries
docker exec pg-biblioteca grep "duration" /var/log/postgresql/postgresql.log | sort -t: -k2 -n | tail
```

### Nginx 502 Bad Gateway

```bash
# Check if API is running
docker ps | grep api

# Check API logs
docker logs api-biblioteca

# Test API directly
docker exec nginx-biblioteca curl -v http://api:8000/health
```

---

## Maintenance & Updates

### Update Application

```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild Docker image
docker-compose build --no-cache

# 3. Restart services
docker-compose down
docker-compose up -d

# 4. Verify
curl http://localhost/health
```

### Update Dependencies

```bash
# Update pip packages
pip install --upgrade -r requirements.txt

# Rebuild image
docker-compose build --no-cache

# Test in staging before production
```

### Zero-Downtime Deployment

```bash
# Using Docker Compose with multiple API instances:
1. docker-compose scale api=2  # Run 2 instances
2. Update 1 instance at a time
3. Nginx automatically routes around updates
```

---

## Support & Documentation

- **API Documentation**: http://localhost/docs (Swagger)
- **Source Code**: https://github.com/[your-repo]
- **Issue Tracking**: [GitHub Issues](https://github.com/[your-repo]/issues)

---

**Last Updated**: 2026-08-28  
**Version**: 1.0
