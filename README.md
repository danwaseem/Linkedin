<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white" />
  <img src="https://img.shields.io/badge/MongoDB-7.0-47A248?style=for-the-badge&logo=mongodb&logoColor=white" />
  <img src="https://img.shields.io/badge/Redis-7.0-DC382D?style=for-the-badge&logo=redis&logoColor=white" />
  <img src="https://img.shields.io/badge/Kafka-3.7-231F20?style=for-the-badge&logo=apachekafka&logoColor=white" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
</p>

<h1 align="center">🔗 LinkedIn Agentic AI Platform</h1>

<p align="center">
  <strong>A distributed LinkedIn-style platform with microservices, Kafka event streaming, Redis caching, and AI-driven hiring workflows powered by local LLMs.</strong>
</p>

<p align="center">
  <em>Built for DATA236 · San Jose State University</em>
</p>

---

## 📑 Table of Contents

- [✨ Project Overview](#-project-overview)
- [🏗️ System Architecture](#️-system-architecture)
- [🛠️ Tech Stack](#️-tech-stack)
- [📂 Repository Structure](#-repository-structure)
- [🚀 Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Step 1: Clone the Repository](#step-1-clone-the-repository)
  - [Step 2: Start Infrastructure](#step-2-start-infrastructure)
  - [Step 3: Configure Environment](#step-3-configure-environment)
  - [Step 4: Set Up Python Environment](#step-4-set-up-python-environment)
  - [Step 5: Seed the Database](#step-5-seed-the-database)
  - [Step 6: Start the Backend](#step-6-start-the-backend)
  - [Step 7: Start the Frontend](#step-7-start-the-frontend)
- [📡 API Documentation](#-api-documentation)
- [🤖 Agentic AI Workflows](#-agentic-ai-workflows)
- [🧪 Running Tests](#-running-tests)
- [✅ Verifying Everything Works](#-verifying-everything-works)
- [⚠️ Troubleshooting & Challenges](#️-troubleshooting--challenges)
- [🏛️ Backend Service Architecture](#️-backend-service-architecture)
- [📊 Kafka Event Topics](#-kafka-event-topics)
- [💡 Development Notes](#-development-notes)
- [👥 Team & Attribution](#-team--attribution)

---

## ✨ Project Overview

This platform models the core functionality of LinkedIn as a **distributed, event-driven system** — not just a CRUD monolith. Every meaningful action (a job being posted, an application submitted, a connection accepted) flows through **Apache Kafka** as a domain event, enabling real-time analytics, asynchronous processing, and system-wide observability.

On top of the traditional services, we built an **Agentic AI layer** — a multi-step AI workflow that uses a local **Ollama LLM** (with graceful regex fallback) to:

1. 📄 **Parse resumes** and extract structured data (skills, experience, education)
2. 🎯 **Match candidates** to jobs using a weighted scoring algorithm
3. ✉️ **Generate personalized outreach** messages for recruiters
4. 👤 **Human-in-the-loop approval** before any action is taken

### What Makes This Different

| Feature | Description |
|---------|-------------|
| **Event-Driven Architecture** | Every state change publishes to Kafka — not just for logging, but for real processing |
| **Idempotent Consumers** | Kafka consumer uses MongoDB to deduplicate events, ensuring at-least-once safety |
| **Redis Query Caching** | Member profiles and job searches are cached with 60–300s TTL, invalidated on writes |
| **Multi-Step AI Agent** | Supervisor pattern: parse → match → rank → outreach, with WebSocket progress streaming |
| **Human-in-the-Loop** | AI output requires recruiter approval before any recruiter-facing action |
| **Graceful Degradation** | Every AI skill falls back to heuristics when Ollama is unavailable |

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           React + Vite Frontend                              │
│               (Job Search, Member Profiles, AI Dashboard)                    │
└────────────────────────────────┬─────────────────────────────────────────────┘
                                 │  HTTP + WebSocket
┌────────────────────────────────▼─────────────────────────────────────────────┐
│                          FastAPI Backend (Port 8000)                         │
│                                                                              │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Profile  │ │   Job    │ │Application │ │Messaging │ │   Connection     │ │
│  │ Service  │ │ Service  │ │  Service   │ │ Service  │ │    Service       │ │
│  └──────────┘ └──────────┘ └────────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌────────────────────────────────────────────┐   │
│  │Recruiter │ │Analytics │ │           AI Agent Service                 │   │
│  │ Service  │ │ Service  │ │  Resume Parser → Job Matcher → Outreach   │   │
│  └──────────┘ └──────────┘ └────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────────────────────┤
│                         Apache Kafka (Event Bus)                             │
│   Topics: job.* │ application.* │ connection.* │ message.* │ ai.*           │
├───────────────┬────────────────────────────┬─────────────────────────────────┤
│    MySQL 8    │        MongoDB 7           │          Redis 7                │
│ (relational)  │  (events, traces, dedup)   │     (query cache)              │
└───────────────┴────────────────────────────┴─────────────────────────────────┘
        ▲                                              ▲
        │              ┌──────────┐                    │
        └──────────────│  Ollama  │────────────────────┘
                       │  (LLM)  │   optional — regex fallback
                       └──────────┘
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.9+ | Core application language |
| **FastAPI** | 0.115 | Async REST framework with auto-generated OpenAPI docs |
| **SQLAlchemy** | 2.0 | ORM for MySQL with connection pooling |
| **Pydantic** | v2 | Request/response validation with rich JSON Schema examples |
| **aiokafka** | 0.11 | Async Kafka producer and consumer |
| **Motor** | 3.6 | Async MongoDB driver for event logs and AI traces |
| **redis-py** | 5.1 | Redis caching with JSON serialization |
| **httpx** | 0.27 | Async HTTP client for Ollama API calls |
| **Faker** | 30.x | Synthetic data generation (10K+ records) |

### Infrastructure
| Technology | Version | Purpose |
|-----------|---------|---------|
| **MySQL** | 8.0 | Relational data (members, jobs, applications, messages, connections) |
| **MongoDB** | 7.0 | Event logs, Kafka consumer idempotency, AI agent traces |
| **Redis** | 7 (Alpine) | Query caching for search results and member profiles |
| **Apache Kafka** | 3.7 (KRaft) | Async event streaming — no Zookeeper needed |
| **Docker Compose** | v2 | Container orchestration for all infrastructure |

### AI & Agent Layer
| Technology | Purpose |
|-----------|---------|
| **Ollama** | Local LLM inference (llama3.2 or any model) |
| **Resume Parser** | Extracts structured fields from resume text |
| **Job Matcher** | Weighted scoring: skills (50%), location (20%), seniority (30%) |
| **Outreach Generator** | Personalized recruiter messages |
| **Hiring Assistant** | Supervisor agent orchestrating the full workflow |

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| **React** | 19 | UI framework |
| **Vite** | 8 | Build tool and dev server |
| **TypeScript** | 5.x | Type-safe frontend development |

---

## 📂 Repository Structure

```
linkedin-agentic-ai/
├── 📦 docker-compose.yml           # MySQL, MongoDB, Redis, Kafka (all infra)
├── 📄 .env.example                  # Template — copy to backend/.env
│
├── 🐍 backend/
│   ├── main.py                      # FastAPI app entry point
│   ├── config.py                    # Centralized settings (pydantic-settings)
│   ├── database.py                  # MySQL (SQLAlchemy) + MongoDB (Motor)
│   ├── cache.py                     # Redis caching layer
│   ├── kafka_producer.py            # Async Kafka event publisher
│   ├── kafka_consumer.py            # Idempotent event consumer
│   ├── requirements.txt             # Python dependencies
│   ├── seed_data.py                 # Synthetic data generator
│   │
│   ├── 📁 models/                   # SQLAlchemy ORM models
│   │   ├── member.py                #   Members + ProfileViewDaily
│   │   ├── recruiter.py             #   Recruiter accounts
│   │   ├── job.py                   #   JobPosting + SavedJob
│   │   ├── application.py           #   Applications
│   │   ├── message.py               #   Threads + Messages
│   │   └── connection.py            #   Connections
│   │
│   ├── 📁 schemas/                  # Pydantic request/response schemas
│   │   ├── member.py, recruiter.py, job.py, application.py
│   │   ├── message.py, connection.py, analytics.py
│   │
│   ├── 📁 routers/                  # API route handlers (8 services)
│   │   ├── members.py               #   /members/* — CRUD + search
│   │   ├── recruiters.py            #   /recruiters/* — CRUD
│   │   ├── jobs.py                  #   /jobs/* — CRUD + search + save
│   │   ├── applications.py          #   /applications/* — submit + status
│   │   ├── messages.py              #   /threads/* + /messages/*
│   │   ├── connections.py           #   /connections/* — request/accept
│   │   ├── analytics.py             #   /analytics/* + /events/*
│   │   └── ai_service.py            #   /ai/* — agentic workflows
│   │
│   ├── 📁 agents/                   # Agentic AI layer
│   │   ├── hiring_assistant.py      #   Supervisor agent (orchestrator)
│   │   ├── resume_parser.py         #   Ollama LLM + regex fallback
│   │   ├── job_matcher.py           #   Weighted match scoring
│   │   └── outreach_generator.py    #   Personalized message generation
│   │
│   ├── 📁 db/
│   │   └── init.sql                 #   MySQL schema (auto-loaded by Docker)
│   │
│   └── 📁 tests/                    # Pytest integration tests
│
├── ⚛️ frontend/                     # React + Vite + TypeScript
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
│
├── 📮 postman/                      # Postman collection + environment
│   ├── LinkedIn_Platform_API.postman_collection.json
│   └── Local.postman_environment.json
│
└── 📄 docs/
    └── openapi.json                 # Static OpenAPI spec
```

---

## 🚀 Getting Started

### Prerequisites

Before you begin, make sure you have:

- ✅ **Docker Desktop** (or Docker Engine + Compose plugin) — [Install Docker](https://docs.docker.com/get-docker/)
- ✅ **Python 3.9+** — [Install Python](https://www.python.org/downloads/)
- ✅ **Node.js 18+** and npm — [Install Node](https://nodejs.org/)
- 🔧 *(Optional)* **[Ollama](https://ollama.com/)** — for full LLM-powered AI features

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/Akashkumarsenthil/Linkedin.git
cd Linkedin
```

---

### Step 2: Start Infrastructure

From the **repo root** (where `docker-compose.yml` lives):

```bash
docker compose up -d
```

This spins up **4 containers**:

| Container | Service | Port |
|-----------|---------|------|
| `linkedin-mysql` | MySQL 8.0 | 3306 |
| `linkedin-mongodb` | MongoDB 7 | 27017 (or 27018 if changed) |
| `linkedin-redis` | Redis 7 | 6379 |
| `linkedin-kafka` | Apache Kafka 3.7 (KRaft) | 9092, 9094 |

**Wait for MySQL to be healthy:**

```bash
docker compose ps
# linkedin-mysql should show "healthy"
```

> 💡 **First run only:** MySQL auto-loads `backend/db/init.sql` to create all tables. If you ever need a fresh database, run `docker compose down -v` to wipe volumes and restart.

---

### Step 3: Configure Environment

```bash
cp .env.example backend/.env
```

The defaults match the Docker Compose configuration. **Key values:**

| Variable | Default | Notes |
|----------|---------|-------|
| `MYSQL_HOST` | `localhost` | |
| `MYSQL_PORT` | `3306` | |
| `MYSQL_USER` | `linkedin_user` | |
| `MYSQL_PASSWORD` | `linkedin_pass` | |
| `MONGO_PORT` | `27017` | Change to `27018` if you have a local MongoDB on 27017 |
| `MONGO_USER` | `mongo_user` | |
| `MONGO_PASSWORD` | `mongo_pass` | |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9094` | Use the **EXTERNAL** listener port |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Only needed if Ollama is installed |
| `OLLAMA_MODEL` | `llama3.2` | Can be changed to any Ollama model |

---

### Step 4: Set Up Python Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

### Step 5: Seed the Database

**Quick seed** (for fast testing — ~500 records):

```bash
python seed_data.py --quick --yes
```

**Full seed** (10,000+ records — takes a few minutes):

```bash
python seed_data.py --yes
```

This generates:
- 10,000 member profiles with realistic skills, experience, and resume text
- 500 recruiter accounts across 30+ companies
- 10,000 job postings with varied skills, locations, and salary ranges
- 15,000+ job applications with realistic status distribution
- 20,000 connections between members
- 2,000 messaging threads with multiple messages each
- 5,000 saved jobs and 30,000 daily profile view records

---

### Step 6: Start the Backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:

```
============================================================
  LinkedIn Agentic AI Platform v1.0.0
============================================================
✓ Kafka producer connected
✓ Kafka consumer started
✓ All services ready
  Swagger UI:  http://localhost:8000/docs
  ReDoc:       http://localhost:8000/redoc
============================================================
```

- 🔗 **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- 📖 **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- ❤️ **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

### Step 7: Start the Frontend

```bash
cd ../frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The Vite dev server proxies `/api` → `http://127.0.0.1:8000`.

---

## 📡 API Documentation

### Swagger / OpenAPI

The best way to explore the API is through the **live Swagger UI** at [http://localhost:8000/docs](http://localhost:8000/docs) while the server is running.

### Postman Collection

We provide a comprehensive Postman collection with **45+ pre-configured requests**:

1. Open Postman
2. Import `postman/LinkedIn_Platform_API.postman_collection.json`
3. Import `postman/Local.postman_environment.json`
4. Select the **Local** environment
5. Start sending requests!

The collection is organized by service and includes:
- ✅ Happy-path workflows
- ❌ Error case tests (duplicate emails, duplicate applications, self-connections)
- 📝 Realistic example payloads ready to execute

### API Endpoints Summary

| Service | Endpoints | Description |
|---------|-----------|-------------|
| **Profile** | `/members/create`, `get`, `update`, `delete`, `search` | Member CRUD + keyword/skill/location search |
| **Recruiter** | `/recruiters/create`, `get`, `update`, `delete` | Recruiter account management |
| **Job** | `/jobs/create`, `get`, `update`, `search`, `close`, `save`, `byRecruiter` | Full job lifecycle |
| **Application** | `/applications/submit`, `get`, `byJob`, `byMember`, `updateStatus`, `addNote` | Application workflow |
| **Messaging** | `/threads/open`, `get`, `byUser` · `/messages/send`, `list` | Threaded messaging |
| **Connection** | `/connections/request`, `accept`, `reject`, `list`, `mutual` | Social connections |
| **Analytics** | `/events/ingest` · `/analytics/jobs/top`, `funnel`, `geo`, `member/dashboard` | Event tracking + dashboards |
| **AI Agent** | `/ai/parse-resume`, `match`, `analyze-candidates`, `task-status`, `approve`, `tasks/list` | Agentic AI workflows |

---

## 🤖 Agentic AI Workflows

The AI system follows a **Supervisor Agent** pattern with human-in-the-loop approval:

```
┌─────────────┐     ┌───────────────┐     ┌──────────────┐     ┌──────────────┐
│   Recruiter │     │ Resume Parser │     │  Job Matcher │     │   Outreach   │
│   triggers  │────►│  (Ollama/     │────►│  (weighted   │────►│  Generator   │
│   analysis  │     │   regex)      │     │   scoring)   │     │  (LLM/       │
│             │     │               │     │              │     │   template)  │
└─────────────┘     └───────────────┘     └──────────────┘     └──────────────┘
                                                                       │
                                                                       ▼
                                                              ┌──────────────┐
                                                              │   Recruiter  │
                                                              │   Approval   │
                                                              │  (human in   │
                                                              │   the loop)  │
                                                              └──────────────┘
```

**How it works:**

1. **`POST /ai/analyze-candidates`** — Kicks off the workflow for a specific job posting
2. The **Hiring Assistant** (supervisor) orchestrates three skills in sequence
3. **Resume Parser** extracts structured data from each candidate's resume
4. **Job Matcher** computes a weighted match score:
   - Skills overlap: **50%**
   - Location compatibility: **20%**
   - Seniority alignment: **30%**
5. Top candidates are ranked and **outreach drafts** are generated
6. Results are published to Kafka (`ai.results` topic) and stored in MongoDB
7. **`POST /ai/approve`** — Recruiter reviews and approves/rejects the output

**WebSocket Support:** Connect to `/ai/ws/{task_id}` for real-time progress updates.

> 💡 **No Ollama? No problem.** Every AI skill has a built-in fallback:
> - Resume Parser → regex-based extraction
> - Job Matcher → pure algorithmic scoring (always works)
> - Outreach Generator → professional template engine

---

## 🧪 Running Tests

With Docker services running and `backend/.env` configured:

```bash
cd backend
source venv/bin/activate
pytest tests/ -m integration -v
```

Tests validate:
- `GET /` and `GET /health` endpoints
- `POST /jobs/search` and `POST /members/search` with database
- `POST /ai/parse-resume` (works with or without Ollama)
- MongoDB and Redis connectivity

---

## ✅ Verifying Everything Works

After starting the server, run these quick checks:

```bash
# 1. Health check — all services should be "healthy"
curl http://localhost:8000/health

# 2. Search jobs
curl -X POST http://localhost:8000/jobs/search \
  -H "Content-Type: application/json" \
  -d '{"keyword": "engineer", "page": 1, "page_size": 5}'

# 3. AI resume parsing (works without Ollama via regex fallback)
curl -X POST http://localhost:8000/ai/parse-resume \
  -H "Content-Type: application/json" \
  -d '{"resume_text": "John Doe | Senior SWE | john@test.com | 8 years Python Java AWS"}'
```

---

## ⚠️ Troubleshooting & Challenges

### Challenge 1: MongoDB Authentication Failed

**Problem:** The Kafka consumer logs `Authentication failed` when trying to deduplicate events.

**Root Cause:** Docker's `MONGO_INITDB_ROOT_USERNAME` creates the user in the `admin` database, but the MongoDB driver tries to authenticate against the target database (`linkedin`) by default.

**Fix:** We added `?authSource=admin` to the MongoDB connection URL in `config.py`. If you're still seeing this error, check your `backend/.env`:

```env
MONGO_USER=mongo_user
MONGO_PASSWORD=mongo_pass
```

### Challenge 2: Kafka Image Not Found (Bitnami)

**Problem:** `bitnami/kafka:3.7` was unavailable on Docker Hub during development.

**Fix:** Switched to the official `apache/kafka:3.7.0` image with proper KRaft-mode environment variables. No Zookeeper required.

### Challenge 3: Kafka Consumer Hanging on Restart

**Problem:** After an ungraceful shutdown, the Kafka consumer would hang for 45+ seconds waiting for the group session to expire before rebalancing.

**Fix:** Added aggressive session timeouts to the consumer config:
```python
session_timeout_ms=10000,
heartbeat_interval_ms=3000,
request_timeout_ms=15000,
```

### Challenge 4: Port Conflicts (MongoDB 27017)

**Problem:** Many developers have a local MongoDB installation on port 27017, which conflicts with the Docker container.

**Fix:** If you hit this, change the published port in `docker-compose.yml`:
```yaml
ports:
  - "27018:27017"
```
And update `MONGO_PORT=27018` in `backend/.env`.

### Challenge 5: AI Endpoints Timing Out

**Problem:** When Ollama isn't running, the resume parser would wait 60 seconds before falling back to regex.

**Fix:** Reduced the HTTP timeout to 5 seconds so the regex fallback kicks in almost instantly. The user experience is seamless — the API always returns `200` with parsed data.

### Challenge 6: SQLAlchemy ROLLBACK Noise

**Problem:** Every read-only API request shows `ROLLBACK` in the logs, which looks alarming.

**Explanation:** This is **completely normal**. SQLAlchemy uses implicit transactions, and when a session closes without a `commit()`, it emits `ROLLBACK` to clean up. No data is lost.

---

## 🏛️ Backend Service Architecture

| Module | Responsibility |
|--------|----------------|
| `main.py` | App factory, CORS, lifespan (Kafka startup/shutdown), health checks |
| `config.py` | Centralized settings from environment via pydantic-settings |
| `database.py` | SQLAlchemy engine + Motor client with connection pooling |
| `cache.py` | Redis caching layer with JSON serialization and TTL support |
| `kafka_producer.py` | Async producer with standardized JSON envelope format |
| `kafka_consumer.py` | Background consumer with MongoDB-backed idempotency |
| `models/` | SQLAlchemy ORM models with `to_dict()` serialization |
| `schemas/` | Pydantic v2 schemas with rich examples for Swagger UI |
| `routers/` | 8 service routers implementing all business logic |
| `agents/` | 4 AI modules: supervisor + 3 skills (parse, match, outreach) |

---

## 📊 Kafka Event Topics

All messages follow a standard JSON envelope:

```json
{
  "event_type": "application.submitted",
  "trace_id": "uuid",
  "timestamp": "2026-04-02T21:30:00Z",
  "actor_id": "42",
  "entity": { "entity_type": "application", "entity_id": "123" },
  "payload": { "job_id": 1, "member_id": 42 },
  "idempotency_key": "uuid"
}
```

| Topic | Triggered By |
|-------|-------------|
| `job.created` | New job posting created |
| `job.viewed` | Member views a job |
| `job.saved` | Member saves a job |
| `job.closed` | Recruiter closes a posting |
| `application.submitted` | New application submitted |
| `application.statusChanged` | Status updated (reviewing → interview → offer) |
| `message.sent` | New message in a thread |
| `connection.requested` | Connection request sent |
| `connection.accepted` | Connection accepted |
| `ai.requests` | AI workflow triggered |
| `ai.results` | AI workflow step completed |

---

## 💡 Development Notes

- **CORS** is wide open (`*`) for development and class demos. Lock this down for any production deployment.
- **Kafka consumer** runs inside the API process for simplicity. In production, you'd run separate consumer workers.
- **`.env` files** are gitignored — always copy from `.env.example` and keep secrets local.
- **Debug mode** (`DEBUG=True` in config) enables SQLAlchemy query logging. Set to `False` to reduce log noise.
- **Redis TTL** defaults: member profiles (300s), job searches (60s). Caches are invalidated on create/update/delete operations.

---

## 👥 Team & Attribution

Built for **DATA236** at **San Jose State University**.

| Role | Focus Area |
|------|-----------|
| Backend Architecture | FastAPI services, database design, Kafka integration |
| AI & Agent Layer | Ollama integration, resume parsing, job matching algorithms |
| Infrastructure | Docker Compose, MySQL/MongoDB/Redis/Kafka setup |
| Frontend | React UI, API integration, WebSocket connectivity |
| Documentation | API docs, Postman collection, README |

---

<p align="center">
  <strong>⭐ If this project helped you, give it a star on GitHub!</strong>
</p>

<p align="center">
  <em>If this README and the code disagree, trust the code — and update both in the same commit.</em>
</p>
