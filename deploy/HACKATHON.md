# Hackathon deploy — get your demo URL (~20 min)

Use **Render** (free, no VPS). You will get two URLs; **submit the frontend URL**.

Example submission URLs (yours will differ):

| Service  | URL |
|----------|-----|
| **Demo (submit this)** | `https://storytrace-web.onrender.com` |
| API (internal) | `https://storytrace-api.onrender.com` |

---

## What you need

1. [Render](https://render.com) account (GitHub login)
2. [GitHub repo](https://github.com/Ahmadjajja/storytrace) on `main`
3. API keys from your local `.env`:
   - `FEATHERLESS_API_KEY`
   - `GEMINI_API_KEY`
   - `NEWSAPI_KEY`
   - `SPEECHMATICS_KEY` (optional, for voice)

---

## Steps

### 1. Push latest code

Make sure `main` has `render.yaml`, `docker-compose.prod.yml`, and `deploy/`.

### 2. Create Blueprint on Render

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. **New** → **Blueprint**
3. Connect **Ahmadjajja/storytrace**, branch **main**
4. Render reads `render.yaml` and creates 3 resources (DB + API + Web)
5. When prompted, enter secret env vars:
   - `FEATHERLESS_API_KEY`, `GEMINI_API_KEY`, `NEWSAPI_KEY`
   - `SPEECHMATICS_KEY` (or leave empty)
   - `WEBHOOK_URL` (optional)

### 3. Run database migration (once)

When **storytrace-db** is live:

1. Open **storytrace-api** → **Shell**
2. Run:

```bash
psql "$DATABASE_URL" -f backend/db/migrations.sql
```

(If tables already exist, skip or ignore “already exists” errors.)

### 4. Wire frontend → API

1. Open **storytrace-api** → copy its public URL, e.g. `https://storytrace-api.onrender.com`
2. Open **storytrace-web** → **Environment** → set:
   ```
   NEXT_PUBLIC_API_URL=https://storytrace-api.onrender.com
   ```
   (no trailing slash, no `/api` prefix)
3. **Manual Deploy** on **storytrace-web** (rebuild required — this is baked at build time)

### 5. Allow CORS on API

On **storytrace-api** → **Environment**:

```
CORS_ORIGINS=https://storytrace-web.onrender.com
```

Use your real frontend hostname from step 4. **Save** and redeploy API if needed.

### 6. Test

```bash
curl https://storytrace-api.onrender.com/health
# {"status":"ok"}
```

Open the **frontend URL** in a browser → enter a topic → wait for the story page.

**Hackathon submission URL:** the frontend URL from step 4.

---

## Notes

- **Free tier cold start:** first load after ~15 min idle can take 30–60s. Wake the API once before demo: `curl .../health`
- **Build time:** first Docker build ~10–15 min (spaCy model).
- **Vultr / single URL:** see [DEPLOY.md](./DEPLOY.md) if you prefer one domain with Nginx.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Frontend “Server error” | Check `NEXT_PUBLIC_API_URL` matches API URL; redeploy frontend |
| CORS error in browser | Set `CORS_ORIGINS` to exact frontend origin (https, no trailing slash) |
| 502 on API | Check API logs; often missing `DATABASE_URL` or failed migration |
| Analyze never completes | API logs — usually missing `FEATHERLESS_API_KEY` or `GEMINI_API_KEY` |
