# SmilAI — Offline Virtual-Teacher & Assessment Platform

> **Powered by Razel Tech** 🇮🇳 | 100% Offline | LAN-Deployable | Voice Interactive

SmilAI is a fully offline virtual-teacher platform designed for local network deployment in government and private schools. It empowers institutions to set up personalized, infinite-patience virtual mentors (teachers) scoped to specific subject syllabi, textbooks, and grading rubrics.

---

## Architecture

```
smilai/
├── frontend/          # React 19 + Vite + TailwindCSS v4
│   └── src/
│       ├── App.tsx
│       ├── components/
│       │   ├── common/     (Auth, Header, Footer)
│       │   └── dashboard/  (Student, Teacher, Admin dashboards)
│       └── types.ts
├── backend/           # Python 3.11+ FastAPI
│   └── src/python/app/
│       ├── main.py         (FastAPI app + lifespan)
│       ├── api/            (auth, chat, content, assessments, voice, admin)
│       ├── database/       (connection.py, vector_db.py, schema.sql)
│       └── rag/            (ingest, retrieve, inference, coding_brain)
├── docs/              # PRD, SRS, Rules, Phase Plans
├── start.bat          # One-click launcher (Ollama + Backend + Frontend)
└── .env.example       # Environment configuration template
```

---

## Quick Start

### Prerequisites
- **Python 3.11+** with a virtual environment in `backend/.venv`
- **Node.js 18+** with npm
- **Ollama** installed and a model pulled (e.g., `ollama pull qwen2.5:7b`)

### 1. Clone & Install
```bash
git clone https://github.com/razeltech/SmilAi.git
cd SmilAi

# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install fastapi uvicorn bcrypt pyjwt pydantic[email] httpx chromadb sentence-transformers rank-bm25 PyMuPDF

# Frontend
cd ../frontend
npm install
```

### 2. Launch Everything
```bash
# From the project root:
.\start.bat
```
This starts **Ollama**, the **FastAPI backend** (port 8000), and the **Vite dev server** (port 5173).

### 3. Demo Accounts
The database auto-seeds with these accounts (password: `password`):

| Role | Email | Name |
|------|-------|------|
| Student | `rahul@school.org` | Rahul Kumar |
| Teacher | `sharma@school.org` | Mr. Sharma |
| Admin | `admin@school.org` | School Administrator |

---

## Core Features

- **Staged Hybrid RAG**: SQL pre-filter → ChromaDB vector search → Cross-Encoder reranking
- **Streaming Chat** (SSE): Humanized latency with filler phrases while RAG processes
- **Voice Interaction**: Browser STT (Speech-to-Text) + TTS (Text-to-Speech), 100% offline
- **Assessment Generation**: Auto-generates MCQ quizzes from uploaded curriculum PDFs
- **Code Grading**: Static AST analysis + LLM rubric feedback (no code execution)
- **Multi-tenant**: All data scoped by `org_id` and `subject_id`

---

## 💾 Saving C-Drive Space: Storing Ollama Models Inside Project Folder

Force Ollama to store models in the project directory:

```powershell
# PowerShell
$env:OLLAMA_MODELS = "D:\ReactApps2Git\smilai\.models"
ollama serve
```

---

## API Documentation

With the backend running, visit: **http://localhost:8000/docs** for the interactive Swagger UI.

Key endpoints:
- `POST /v1/auth/login` — JWT authentication
- `POST /v1/chat/stream` — Streaming RAG chat
- `GET /v1/subjects` — List subjects by user role
- `POST /v1/content/upload` — Teacher PDF upload
- `POST /v1/assessments/generate` — Auto-generate quizzes
- `POST /v1/coding/analyze` — Static code grading

---

## Documentation

| Document | Purpose |
|----------|---------|
| [SmilAI_rules.md](docs/SmilAI_rules.md) | Architecture rules & non-negotiables |
| [SmilAI_PRD.md](docs/SmilAI_PRD.md) | Product Requirements Document |
| [SmilAI_SRS.md](docs/SmilAI_SRS.md) | Software Requirements Specification |
| [EXPECTED_OUTCOMES.md](docs/EXPECTED_OUTCOMES.md) | Vision & user scenarios |
| [SmilAI_PHASE_PLAN.md](docs/SmilAI_PHASE_PLAN.md) | Development phases & timeline |
