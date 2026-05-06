# Telegram Qdrant Semantic Search

A complete toolkit for backing up a Telegram chat/topic, automatically expanding shared embedded links/tweets, and making them fully searchable using AI Embeddings and Qdrant!

## Prerequisites
- A Telegram account with [API ID and Hash](https://my.telegram.org/)
- [Docker](https://www.docker.com/) (to run the Qdrant vector database)
- Python 3.9+

## Quick-Start Checklist

### 1. Install Dependencies
```bash
python3 -m venv .venv
# Activate:
# Linux/Mac: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Credentials
```bash
cp .env.example .env
```
Edit `.env` with your your `TG_API_ID`, `TG_API_HASH`, `TG_PHONE` and optionally the `TG_GROUP` (can be an `@username` or ID).

### 3. Backup Telegram Messages
You can run it interatively, or provide direct flags:
```bash
python backup.py --topic 1 --limit 1000 --no-media
```
_This will create a `backup_X.json` inside the `backup/` directory._

### 4. Parse URLs
Extracts URLs from messages, automatically unwraps `x.com` / `twitter.com` via `fixupx.com` to grab the text, and crawls `<title>` tags for other links.
```bash
python parse_urls.py
```
_It automatically discovers your latest backup file if no explicit path is provided._

### 5. Start Qdrant Vector Database
Spins up Qdrant locally in the background.
```bash
docker compose up -d
```

### 6. Ingest into Database
Injects your URLs into Qdrant as semantic vectors using the lightweight `BAAI/bge-small-en-v1.5` model.
```bash
python ingest_qdrant.py
```

### 7. Search
Run a semantic query natively from the command line:
```bash
python query.py "nvidia gpu" --top 3
```
_(Alternatively, you can visually explore your vectors by opening http://localhost:6333/dashboard in your browser!)_
