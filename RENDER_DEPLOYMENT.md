# Biblioteca de Seguridad de Procesos — Deployment

## Local Development

```bash
# Start with Docker Compose
./start.bat  # Windows
bash start.sh  # macOS/Linux

# API will be at http://localhost:8000
# Docs at http://localhost:8000/docs
```

## Deployment on Render.com

### Prerequisites
- GitHub repository connected to Render
- Groq API key

### Steps

1. **Create Web Service** on Render.com
   - Connect your GitHub repository
   - Build command: (leave empty - uses Dockerfile)
   - Start command: `./start.sh`
   - Add environment variables:
     - `GROQ_API_KEY` = your Groq API key
     - `GROQ_MODEL` = openai/gpt-oss-120b

2. **Create PostgreSQL Database** on Render.com
   - Region: same as Web Service (for performance)
   - Postgres version: 16+
   - Copy the `DATABASE_URL` to Web Service environment variables

3. **Add Volumes** (if needed for persistence)
   - Render automatically creates a volume for PostgreSQL

4. **Deploy**
   - Push to GitHub
   - Render automatically deploys on every push to `main` branch

### Environment Variables Required

```env
# Groq API
GROQ_API_KEY=gsk_YOUR_API_KEY
GROQ_MODEL=openai/gpt-oss-120b

# Database (provided by Render PostgreSQL)
DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db
```

### Estimated Costs

- **Web Service**: $7-12/month (starter plan)
- **PostgreSQL Database**: $7-15/month (starter plan with 10GB)
- **Total**: ~$14-27/month

### Important Notes

⚠️ **Production Considerations:**
- The free tier has memory limitations (~512MB) - may not be enough for large embeddings
- Use `paid` plans for production workloads
- Database backups available on paid plans
- Add monitoring and error tracking (Sentry, LogRocket, etc.)

### Troubleshooting

If deployment fails:
1. Check the build logs in Render dashboard
2. Verify all environment variables are set
3. Ensure PostgreSQL service is running first
4. Check that `DATABASE_URL` format is correct

### Scaling

For production:
- Use Render's Standard/Professional plans
- Add Redis for caching (optional)
- Implement rate limiting
- Add authentication to API endpoints
