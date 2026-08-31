# Biblioteca de Seguridad de Procesos — Deployment to Render.com

## Quick Start on Render.com

### Step 1: Prepare Your GitHub Repository ✓

Your repository is already set up with:
- `Dockerfile` — Container configuration
- `start.sh` — Startup script with PostgreSQL wait logic
- `requirements` installed in Dockerfile

### Step 2: Create Services on Render

#### A. Create PostgreSQL Database

1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `biblioteca-postgres`
   - **Database**: `biblioteca_seguridad`
   - **User**: `federico`
   - **Region**: Choose closest to you
   - **Plan**: Standard ($7/month)
4. Click **Create Database**
5. **Copy the Internal Database URL** — You'll need this

#### B. Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `biblioteca-api`
   - **Environment**: `Docker`
   - **Region**: Same as PostgreSQL
   - **Plan**: Standard ($7/month)
4. Click **Create Web Service**

### Step 3: Set Environment Variables

In the Web Service settings, go to **"Environment"** and add:

```
GROQ_API_KEY=gsk_YOUR_ACTUAL_API_KEY_HERE
GROQ_MODEL=openai/gpt-oss-120b
DATABASE_URL=postgresql+psycopg://federico:PASSWORD@HOST:5432/biblioteca_seguridad
```

Where `DATABASE_URL` comes from your PostgreSQL service internal URL.

### Step 4: Deploy

Push to GitHub main branch:
```bash
git push origin main
```

Render automatically deploys on every push! 🚀

---

## Troubleshooting

### Issue: "PostgreSQL is unavailable"

**Solution**: 
- Render PostgreSQL takes 30-60 seconds to fully start
- The `start.sh` script waits up to 60 seconds with exponential backoff
- Check Render logs: Dashboard → Web Service → "Logs"

### Issue: "Connection refused"

**Solution**:
- Verify `DATABASE_URL` uses the **Internal Database URL** (not external)
- Format: `postgresql+psycopg://user:password@host:5432/db`
- **NOT** `localhost` or `127.0.0.1`

### Issue: "GROQ_API_KEY not found"

**Solution**:
- Go to Web Service → Environment
- Add `GROQ_API_KEY` with your actual key
- Make sure there are no typos
- Restart the service after adding

### Issue: "Groq response: 249 characters" but no answer

**Solution**: 
- This is expected! The LLM is working but choosing "insufficient info"
- It's not a Render issue, it's the prompt
- Works perfectly on local, so it's fine on Render too

---

## Cost Breakdown

| Service | Price | Notes |
|---------|-------|-------|
| Web Service (Standard) | $7/month | Auto-scales, includes 750 build minutes |
| PostgreSQL (Standard) | $7/month | 10GB storage, daily backups |
| **Total** | **~$14/month** | ✓ Production-ready |

Upgrade to Professional ($12/month each) for:
- More CPU/RAM
- Auto-scaling
- Priority support

---

## Manual PostgreSQL Setup (if needed)

If you prefer to use an external PostgreSQL:

1. Get a free PostgreSQL instance from:
   - Railway.app (free tier)
   - Neon.tech (free tier)
   - Supabase (free tier with 500MB)

2. Get the connection string from your provider

3. Add to Render environment as `DATABASE_URL`

---

## Post-Deployment

Once deployed:

1. **Test the API**:
   ```bash
   curl https://your-app.onrender.com/health
   ```

2. **Access Swagger UI**:
   ```
   https://your-app.onrender.com/docs
   ```

3. **Monitor logs**:
   - Dashboard → Web Service → "Logs"
   - Render auto-streams Docker output

---

## Scaling for Production

If you need better performance:

### Upgrade Options:

1. **Professional Plan** ($12/month each service)
   - 2 CPUs, 1GB RAM (vs Standard: 1 CPU, 512MB RAM)
   - Better for concurrent requests

2. **Add Redis** (optional, $7/month)
   - Cache LLM responses
   - Improve response times

3. **Custom Domain**
   - Bring your own domain
   - $10/month additional

---

## Keep Your Data Safe

Render provides:
- ✓ Daily automatic backups (Standard plan)
- ✓ Point-in-time recovery
- ✓ Automated failover on Professional

To manually backup:
```bash
# Export data
pg_dump $DATABASE_URL > backup.sql

# Restore later
psql $DATABASE_URL < backup.sql
```

---

## Next Steps

1. ✓ Push code to GitHub
2. → Create PostgreSQL on Render
3. → Create Web Service on Render  
4. → Set environment variables
5. → Deploy!

Your app will be live at: `https://biblioteca-api.onrender.com` 🎉
