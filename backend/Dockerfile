FROM python:3.14-slim

WORKDIR /app

# Install deps first (cached layer — only re-runs when requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy English model required by seed_agent and crawler_agent
RUN python -m spacy download en_core_web_sm

# Copy the full repo (build context is repo root, not ./backend)
COPY . .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
