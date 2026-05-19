# Deploy StoryTrace (VPS + Docker)

StoryTrace runs as three containers (Postgres, FastAPI, Next.js) behind Nginx on a single VPS. This matches the hackathon spec (Vultr Ubuntu 22.04).

## What you need

| Item | Notes |
|------|--------|
| **VPS** | Ubuntu 22.04+, 2 GB+ RAM recommended (spaCy + Next build) |
| **Domain** (optional) | Point A record to VPS IP for HTTPS |
| **API keys** | Same as local `.env` — see `.env.example` |

## 1. Provision the server

SSH in as root or a sudo user:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-plugin nginx certbot python3-certbot-nginx git
sudo usermod -aG docker $USER
# Log out and back in so docker group applies
```

## 2. Clone and configure

```bash
git clone https://github.com/Ahmadjajja/storytrace.git
cd storytrace
git checkout main

cp .env.example .env
nano .env
```

Set these for **production** (replace `YOUR_DOMAIN_OR_IP` with your public IP or domain):

```bash
# Strong password for Postgres (used by docker-compose.prod.yml)
POSTGRES_PASSWORD=choose-a-long-random-password

# Browser calls API through Nginx at /api
NEXT_PUBLIC_API_URL=http://YOUR_DOMAIN_OR_IP/api

# If you use HTTPS after certbot:
# NEXT_PUBLIC_API_URL=https://yourdomain.com/api

DATABASE_URL=postgresql://postgres:YOUR_POSTGRES_PASSWORD@db:5432/storytrace
FEATHERLESS_API_KEY=...
GEMINI_API_KEY=...
NEWSAPI_KEY=...
SPEECHMATICS_KEY=...
WEBHOOK_URL=...
```

Fill in all keys from your local `.env`. Do **not** commit `.env`.

## 3. Build and start

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Wait for builds to finish (first run can take several minutes). Check status:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api
curl -s http://127.0.0.1:8000/health
```

## 4. Configure Nginx

```bash
sudo cp deploy/nginx/storytrace.conf /etc/nginx/sites-available/storytrace
sudo nano /etc/nginx/sites-available/storytrace
# Change YOUR_DOMAIN_OR_IP to your IP or domain

sudo ln -sf /etc/nginx/sites-available/storytrace /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Open `http://YOUR_DOMAIN_OR_IP` in a browser. Submit a topic to verify the pipeline.

## 5. HTTPS (recommended)

```bash
sudo certbot --nginx -d yourdomain.com
```

After SSL, update `.env`:

```bash
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
```

Rebuild the frontend (API URL is baked in at build time):

```bash
docker compose -f docker-compose.prod.yml up -d --build frontend
```

## 6. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

Only ports 22, 80, and 443 should be public. API (8000) and frontend (3000) bind to `127.0.0.1` only.

## Updates

```bash
cd storytrace
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Frontend can't reach API | `NEXT_PUBLIC_API_URL` must be `http(s)://HOST/api` (same host as the site) |
| `502 Bad Gateway` | `docker compose -f docker-compose.prod.yml ps` — wait for `api` / `frontend` healthy |
| DB connection errors | Check `POSTGRES_PASSWORD` matches in `.env` and `DATABASE_URL` |
| Voice input fails | `SPEECHMATICS_KEY` must be set; route is server-side in Next.js |
| Analyze hangs / fails | `docker compose -f docker-compose.prod.yml logs api` — often missing API keys |

## Alternative: split hosting

Not covered by default config, but possible:

- **Frontend**: Vercel (`frontend/`, set `NEXT_PUBLIC_API_URL` to your API URL)
- **Backend**: Railway / Render / Fly.io (run `uvicorn backend.main:app`, managed Postgres)
- Set `CORS_ORIGINS` in backend `.env` to your Vercel URL

For the hackathon demo, the single-VPS Docker + Nginx setup above is simplest.
