# Vultr backend + Render frontend

| Layer | Host | URL |
|-------|------|-----|
| Frontend (submit this) | Render | `https://storytrace-web.onrender.com` |
| API | Vultr VM | `http://YOUR_VULTR_IP:8000` |
| Database | Vultr Managed Postgres | `DATABASE_URL` in API `.env` only |

---

## 1. Vultr — backend (teammate / SSH)

On the Vultr Ubuntu VM:

```bash
git clone https://github.com/Ahmadjajja/storytrace.git
cd storytrace
cp .env.example .env
nano .env
```

Set in `.env`:

```bash
DATABASE_URL=postgresql://vultradmin:PASSWORD@....vultrdb.com:16751/defaultdb
FEATHERLESS_API_KEY=...
GEMINI_API_KEY=...
NEWSAPI_KEY=...
CORS_ORIGINS=https://storytrace-web.onrender.com
WEBHOOK_URL=
```

Start API only:

```bash
docker compose -f docker-compose.vultr.yml up -d --build
curl http://localhost:8000/health
```

Open firewall port **8000** in Vultr cloud firewall + `ufw allow 8000` if using ufw.

Public test:

```bash
curl http://YOUR_VULTR_PUBLIC_IP:8000/health
```

---

## 2. Render — frontend

### Option A — existing `storytrace-web` service

1. **storytrace-web** → **Environment** → add:

   ```
   API_URL=http://YOUR_VULTR_PUBLIC_IP:8000
   ```

   (no trailing slash; use `https://` if you put TLS on Vultr)

2. **Manual Deploy** (no rebuild required for `API_URL` changes after latest code)

3. Suspend/delete **storytrace-api** and **storytrace-db** on Render if unused

### Option B — new Blueprint (frontend only)

1. **+ New** → **Blueprint**
2. Repo **Ahmadjajja/storytrace**, branch **main**
3. **Blueprint path:** `render.frontend.yaml`
4. Set `API_URL` and `SPEECHMATICS_KEY` when prompted

---

## 3. Test

```bash
curl http://YOUR_VULTR_IP:8000/health
```

Open **https://storytrace-web.onrender.com** → run a topic.

---

## Change API later (no frontend rebuild)

Render → **storytrace-web** → change `API_URL` → **Save** → restart service (or redeploy).  
The app reads `API_URL` at runtime via `/api/config`.
