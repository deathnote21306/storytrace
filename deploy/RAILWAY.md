# Deploy StoryTrace on Railway (hackathon)

Use **one Railway project** with **3 services**: Postgres + API + Frontend.

**Submit this URL:** your frontend public URL  
(e.g. `https://storytrace-web-production.up.railway.app`)

---

## 1. Create project

1. Railway dashboard → **+ Create new project**
2. **Deploy from GitHub repo** → choose **Ahmadjajja/storytrace**
3. Branch: **main**

Railway may create one service automatically — we'll add the rest.

---

## 2. Add PostgreSQL

1. Inside the project → **+ New** → **Database** → **PostgreSQL**
2. Name it `postgres` (or any name)

---

## 3. Backend (API) service

If Railway already created a service from the repo, click it and configure.  
Otherwise: **+ New** → **GitHub Repo** → same **storytrace** repo.

**Settings → Source:**

| Setting | Value |
|---------|--------|
| Root Directory | `/` (repo root) |
| Dockerfile Path | `backend/Dockerfile` |

**Settings → Deploy:**

| Setting | Value |
|---------|--------|
| Healthcheck Path | `/health` |

**Variables** (Raw Editor or one-by-one):

```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
FEATHERLESS_API_KEY=<from your .env>
GEMINI_API_KEY=<from your .env>
NEWSAPI_KEY=<from your .env>
WEBHOOK_URL=
CORS_ORIGINS=https://REPLACE_WITH_FRONTEND_DOMAIN
```

Replace `Postgres` with your database service name if different (click Postgres → **Variables** → copy reference syntax).

**Rename service** to `storytrace-api` (Settings → name) so URLs are predictable.

**Deploy** → wait for build (~10–15 min first time).

**Run migrations once:**

1. API service → **Deployments** → latest → **View logs** (confirm running)
2. API service → **Settings** → open **Shell** / one-off command, or use Railway CLI:

```bash
railway run --service storytrace-api psql "$DATABASE_URL" -f backend/db/migrations.sql
```

Or from local machine with Railway CLI linked to the project:

```bash
railway link
railway run psql "$DATABASE_URL" -f backend/db/migrations.sql
```

Test:

```bash
curl https://YOUR-API-DOMAIN.up.railway.app/health
```

---

## 4. Frontend service

**+ New** → **GitHub Repo** → **storytrace** (same repo, second service).

**Settings → Source:**

| Setting | Value |
|---------|--------|
| Root Directory | `frontend` |
| Dockerfile Path | `Dockerfile` |

**Variables:**

```bash
NEXT_PUBLIC_API_URL=https://YOUR-API-DOMAIN.up.railway.app
SPEECHMATICS_KEY=<from your .env>
```

Get API domain: click **storytrace-api** → **Settings** → **Networking** → **Generate Domain** if missing → copy public URL **without** trailing slash.

**Important:** `NEXT_PUBLIC_API_URL` is baked in at **build** time. After changing it, trigger **Redeploy**.

Rename service to `storytrace-web`.

---

## 5. Fix CORS on API

On **storytrace-api** → **Variables**:

```bash
CORS_ORIGINS=https://YOUR-FRONTEND-DOMAIN.up.railway.app
```

Use the exact frontend public URL (from **storytrace-web** → Networking → domain). Redeploy API.

---

## 6. Generate public domains

For **both** API and frontend services:

**Settings** → **Networking** → **Generate Domain** (if not already)

---

## 7. Hackathon submission

| Field | Value |
|-------|--------|
| **Live demo URL** | Frontend domain, e.g. `https://storytrace-web-production.up.railway.app` |
| **Repo** | `https://github.com/Ahmadjajja/storytrace` |

**Before demo:** open API health URL once (wakes the service), then open frontend and run a topic.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Build fails on API | Check deploy logs; need enough memory (upgrade plan if OOM during spaCy install) |
| Frontend can't reach API | `NEXT_PUBLIC_API_URL` must be `https://...` API domain; redeploy frontend after change |
| CORS error | `CORS_ORIGINS` must match frontend URL exactly |
| 500 on analyze | API logs — usually missing API keys or DB migration not run |
| Service sleeps | Railway free/credit usage — hit `/health` before presenting |

---

## Do not use the old project

Create a **new** project for StoryTrace. Don't deploy into **brazilian-laws-chatbot** unless you intentionally replace that app.
