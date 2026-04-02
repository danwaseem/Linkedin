# LinkedIn Agentic AI Platform

> **DATA236 · distributed systems + agentic AI demo**  
> A LinkedIn-style domain modeled as a **FastAPI** monolith (clear service boundaries in code), backed by **MySQL**, **MongoDB**, **Redis**, and **Kafka**, with optional **Ollama** for local LLMs. A **React + Vite** console exercises the same HTTP API you can drive from **Swagger** or **Postman**.

---

## Contents

- [At a glance](#at-a-glance)
- [Architecture](#architecture)
- [Repository map](#repository-map)
- [Tech stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Setup (step by step)](#setup-step-by-step)
- [Running tests](#running-tests)
- [API documentation](#api-documentation)
- [Is everything working?](#is-everything-working)
- [Troubleshooting](#troubleshooting)
- [Backend layout](#backend-layout)
- [Development notes](#development-notes)
- [License / course use](#license--course-use)

---

## At a glance

| Layer | Role |
|--------|------|
| **REST API** | Members, recruiters, jobs, applications, messages, connections, analytics, AI agents |
| **MySQL** | Source of truth for relational entities |
| **MongoDB** | Event logs, idempotency for Kafka consumer, agent traces |
| **Redis** | Query / profile caching |
| **Kafka** | Domain events (`job.created`, `application.submitted`, …) |
| **Ollama** *(optional)* | LLM-backed resume parsing and matching; **automatic regex/heuristic fallback** if Ollama is offline |
| **Frontend** | Small operational UI: health, job/member search, analytics snippet, AI parse demo |

---

## Architecture

```text
┌─────────────┐     HTTP      ┌──────────────────────────────────────────┐
│  React UI   │ ────────────►  │  FastAPI (routers + agents + lifespan)    │
│  (Vite)     │   /api proxy   │  MySQL ◄──► Redis cache                  │
└─────────────┘                │  Mongo ◄── event logs, consumer state    │
                               │  Kafka ◄── producer + background consumer │
└──────────────────────────────────────────┘
         ▲
         │  optional
    ┌────┴────┐
    │ Ollama  │  localhost:11434
    └─────────┘
```

---

## Repository map

| Path | What it is |
|------|------------|
| `backend/` | FastAPI app, SQLAlchemy models, Kafka, agents |
| `backend/db/init.sql` | MySQL schema (loaded by Docker on first MySQL start) |
| `backend/seed_data.py` | Synthetic data (`--quick` for fast smoke tests) |
| `backend/tests/` | Pytest smoke tests (`-m integration`) |
| `docs/openapi.json` | Static OpenAPI 3 spec (regenerate with `backend/scripts/export_openapi.py`) |
| `docker-compose.yml` | MySQL, MongoDB, Redis, Kafka (KRaft) |
| `frontend/` | Vite + React + TypeScript console |
| `postman/` | Collection + **Local** environment (`base_url`) |

---

## Tech stack

- **Python 3.9+** — FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2, aiokafka, redis-py, Motor, httpx  
- **MySQL 8** — transactional data  
- **MongoDB 7** — documents + consumer idempotency  
- **Redis 7** — caching  
- **Apache Kafka 3.7 (KRaft)** — streaming  
- **Ollama** *(optional)* — local models (e.g. `llama3.2`)  
- **Node 18+** — Vite 8, React 19, TypeScript  

---

## Prerequisites

- **Docker Desktop** (or Docker Engine + Compose plugin)  
- **Python 3.9+**  
- **Node 18+** and npm  
- *(Optional)* **[Ollama](https://ollama.com/)** for full LLM behavior on AI routes  

---

## Setup (step by step)

### 1. Clone and open the repo

```bash
git clone <your-remote-url> linkedin-agentic-ai
cd linkedin-agentic-ai
```

### 2. Start infrastructure

From the **repo root** (next to `docker-compose.yml`):

```bash
docker compose up -d
```

Wait until **`linkedin-mysql`** reports **healthy** (`docker ps`).

> **First run only:** MySQL initializes from `backend/db/init.sql`. If you ever need a clean database volume, stop containers and remove the named volume for MySQL (this wipes data).

### 3. Backend environment

```bash
cp .env.example backend/.env
```

Edit `backend/.env` if you changed passwords or ports in Compose.

**Critical values (defaults match this repo’s Compose file):**

| Variable | Typical value | Notes |
|----------|---------------|--------|
| `MYSQL_*` | `localhost:3306`, user `linkedin_user`, DB `linkedin` | |
| `MONGO_PORT` | **`27018`** | Published port in `docker-compose.yml` (see [Troubleshooting](#troubleshooting)) |
| `MONGO_AUTH_SOURCE` | `admin` | Required for Docker’s root user created by `MONGO_INITDB_ROOT_*` |
| `REDIS_HOST` / port | `localhost` / `6379` | |
| `KAFKA_BOOTSTRAP_SERVERS` | **`localhost:9094`** | Host clients use the **EXTERNAL** listener |

### 4. Python virtual environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Seed the database

Quick dataset (good for laptops and CI-style checks):

```bash
python seed_data.py --quick --yes
```

Large dataset (tens of thousands of rows — be patient):

```bash
python seed_data.py --yes
```

### 6. Run the API

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)  
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)  
- **Health:** [http://localhost:8000/health](http://localhost:8000/health)  

### 7. Run the frontend

```bash
cd ../frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The dev server proxies `/api` → `http://127.0.0.1:8000`.

For a static production build, set **`VITE_API_URL`** (see `frontend/.env.example`).

---

## Running tests

With Docker services up and `backend/.env` aligned with Compose:

```bash
cd backend
source venv/bin/activate
pytest tests/ -m integration -v
```

These tests spin up the app **in-process** (Starlette `TestClient`), so Kafka and Mongo connections run as in real startup. They assert:

- `GET /` and `GET /health`  
- `POST /jobs/search` and `POST /members/search`  
- `POST /ai/parse-resume` (works with or without Ollama thanks to fallback)  

---

## API documentation

1. **Live (best while coding):** [http://localhost:8000/docs](http://localhost:8000/docs)  
2. **Static file:** `docs/openapi.json` — open in [Swagger Editor](https://editor.swagger.io/) or feed to codegen. Regenerate:

   ```bash
   backend/venv/bin/python backend/scripts/export_openapi.py
   ```

3. **Postman:** import `postman/LinkedIn_Platform_API.postman_collection.json` and `postman/Local.postman_environment.json`, then select the **Local** environment.

---

## Is everything working?

After `uvicorn` is running, check:

1. **`GET /health`** — `status` should be **`healthy`** when Redis, Kafka producer, and **MongoDB** are all reachable.  
2. **Swagger** — try `POST /jobs/search` with a small JSON body.  
3. **Logs** — a line like `Ollama not available … using regex fallback` on **`/ai/parse-resume`** is **normal** if Ollama is not installed; the response should still be `200` with parsed fields.

---

## Troubleshooting

### MongoDB: `Authentication failed` in `kafka_consumer` or `/health` shows `mongodb: false`

Common causes:

1. **Wrong port — local `mongod` vs Docker**  
   Many developers run **MongoDB locally** on `27017`. Connections to `127.0.0.1:27017` can hit that process instead of the container, so credentials never match.  
   **This repo maps the container to host port `27018`.** Set in `backend/.env`:

   ```env
   MONGO_PORT=27018
   MONGO_AUTH_SOURCE=admin
   ```

   Then `docker compose up -d` (recreate `mongodb` if you changed the mapping).

2. **Wrong auth database**  
   Root users created by `MONGO_INITDB_ROOT_USERNAME` authenticate against the **`admin`** database. The app URI includes `authSource=admin` (see `config.py`).

### Kafka: cannot connect from the host

Use **`KAFKA_BOOTSTRAP_SERVERS=localhost:9094`** (the `EXTERNAL` listener in Compose). Inside Docker networks, services would use `kafka:9092`.

### SQLAlchemy log noise: `ROLLBACK` after a `200 OK`

Read-only requests often end the session without a commit; SQLAlchemy emits `ROLLBACK` when closing the transaction. **This is expected** and not an application error.

### AI routes without Ollama

Install [Ollama](https://ollama.com/), run `ollama pull llama3.2` (or set `OLLAMA_MODEL`), and ensure `OLLAMA_BASE_URL` is reachable. Until then, the API uses **heuristic / regex** parsing — still valid for demos.

---

## Backend layout

| Module / package | Responsibility |
|------------------|------------------|
| `main.py` | App factory, CORS, lifespan (Kafka producer + consumer task), health |
| `config.py` | Settings from environment |
| `database.py` | SQLAlchemy + Motor |
| `cache.py` | Redis |
| `kafka_*.py` | Async producer / consumer |
| `models/`, `schemas/` | ORM + Pydantic |
| `routers/` | HTTP surface per domain |
| `agents/` | Resume, match, outreach, hiring assistant |

---

## Development notes

- **CORS** is wide open for class demos; lock it down for any public deployment.  
- **Kafka consumer** runs in the API process for simplicity; production would typically use separate workers.  
- **`.env`** is gitignored — copy from `.env.example` and keep secrets local.  

---

## License / course use

Built for **DATA236** (LinkedIn Agentic AI). Adjust attribution and licensing to match your course policy.

---

*If this README and the code disagree, trust the code — and update both in the same change.*
