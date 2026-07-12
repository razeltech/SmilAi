# SmilAI — Central Intelligence & Memory Brain

> **CRITICAL DIRECTIVE FOR AI ASSISTANTS**: Read this document completely before proposing any changes. This is the single source of truth for project architecture, database schemas, and codebase mapping.

## 1. Project Vision & Core Directives
SmilAI is a production-grade, on-premise virtual AI teacher platform designed for government and private schools.
1. **Fully Offline & Air-Gapped**: The system must run on-premise without *any* external internet dependencies. No cloud APIs (OpenAI/Anthropic), no external LLM providers.
2. **One Brain, Many Subjects**: One underlying AI persona configured into many subject-specific virtual teachers (Math, Science, Coding Brain, Language Brain). 
3. **Motherly & Gentle Persona**: SmilAI treats the student like a younger brother or sister. She acts like a gentle, incredibly patient mother who teaches without *any* judgement. Students who are afraid to ask questions in class must feel perfectly safe asking her.
4. **Accent & Pronunciation Training**: The system specifically includes Voice Detection and Correction for teaching British and American accent practice.
5. **Local Hardware Constraints**: Assumed hardware is a single RTX 3060 12GB. GPU is a shared, scarce resource. Small models (embeddings/rerankers) should default to CPU threading to prevent VRAM locking.
6. **Strict Local Model Storage**: All AI models (LLMs, Embeddings, STT, TTS, Rerankers) MUST be downloaded exclusively inside the project directory (e.g., `./models/`). Global caching (`~/.cache/huggingface`) is strictly prohibited. Use `HF_HOME` and `OLLAMA_MODELS` variables.
7. **API-First Extensibility**: Like Athena, the API is the product. Our endpoints must be robust and clean enough to support a React UI today, and a Unity/Mobile app tomorrow.

---

## 2. High-Performance RAG Architecture (1M+ Document Scale)
To survive production workloads across thousands of students and millions of PDFs, the system implements **Staged Hybrid Retrieval**.

- **Ingestion & "The Chunk Explosion"**:
  - *Semantic Chunking*: Chunk by meaning/sentences, not by arbitrary token counts.
  - *Document Hierarchy*: Store structural metadata (Doc -> Section -> Chunk).
  - *Deduplication*: Aggressive semantic deduplication to cut index size.
- **The Retrieval Bottleneck (Staged Hybrid Filtering)**:
  - **Stage 1 (Pre-filter)**: SQL/Metadata filtering (e.g., `WHERE subject_id = X AND org_id = Y AND doc_type = 'library'`). This reduces the search space by 90%+ instantly.
  - **Stage 2 (Vector Search + BM25)**: Hybrid search across the filtered subset for semantic meaning and rare keyword matching.
  - **Stage 3 (Post-filter / Reranking)**: A local Cross-Encoder reranker scores the top 50 chunks down to the highest-signal top 5-10 chunks.
- **Context Overload Illusion**:
  - LLMs hallucinate when fed too much context. Only the top 5-10 highly relevant chunks are injected into the prompt.
  - Every injected chunk must enforce citation grounding (e.g., `[Citation 1]`).

---

## 3. Global Tech Stack
- **Frontend**: React 19, Vite, TailwindCSS (v4), TypeScript.
- **Backend (Node.js - Legacy/UI Routes)**: Express, SQLite (`better-sqlite3`).
- **AI Backend (Python - RAG Engine)**: FastAPI, Uvicorn, Python 3.11+, `sqlite3`. Managed via a local `.venv`.

---

## 4. Codebase Map & File Functionalities

### 📂 Root Configurations
- `server.ts`: Node.js Express entrypoint. Mounts Vite middleware for dev and serves static SPA in production. Handles non-AI API routes (`/v1`).
- `package.json` / `vite.config.ts`: React UI build tooling and dependencies.
- `playwright.config.ts`: E2E testing framework configuration.

### 📂 Documentation (`/docs/`)
- `SmilAI_PRD.md`: Product Requirements Document (vision, audience, roadmap phases).
- `SmilAI_SRS.md`: Software Requirements Specification (tech specs, security).
- `SmilAI_rules.md`: Working rules, AI coding constraints (LAN-first, offline-only).
- `PLAN.md` & `SmilAI_PHASE_PLAN.md`: Strategic phase breakdowns.
- `DECISIONS.md` (to be created): Architecture Decision Records (ADRs).
- `memory_brain.md`: (This file).

### 📂 AI & Data Scripts (`/scripts/`)
- `server_python.py`: **The Core AI Backend**. FastAPI server responsible for local LLM inference, embedding generation, Staged Hybrid RAG, and semantic chunking.
- `create_schema.js` & `migrate.js`: SQLite schema initialization and migration scripts.
- `add_subject.js` & `add_teacher.js`: CLI utilities for database seeding.
- `convert_db.js` & `test_db.js`: Database maintenance utilities.

### 📂 UI Backend Routes (`/src/server/`)
- `db.ts`: SQLite schema and connection handlers for Node.js.
- `parsers.ts`: Legacy document extraction tools (migrating to Python).
- `utils/search.ts`: Legacy semantic search logic (migrating to Python).
- **Routes (`/src/server/routes/`)**:
  - `admin.ts`: Organization, subject, and teacher management.
  - `auth.ts`: JWT/Session authentication.
  - `chat.ts`: Legacy chat endpoints (migrating to Python for local streaming).
  - `content.ts`: Document upload endpoints.
  - `assessments.ts` & `academic.ts`: Test generation and auto-grading endpoints.

### 📂 Frontend UI (`/src/components/`)
- `App.tsx`: Main shell handling offline-first session hydration and role-based routing.
- **Dashboards (`/dashboard/`)**:
  - `AdminDashboard.tsx`: UI to assign teachers to subjects, manage org boundaries.
  - `TeacherDashboard.tsx`: UI to bulk-ingest syllabi ("library mode"), set rubrics, and view student progress.
  - `StudentDashboard.tsx`: The primary interaction UI. Students chat with SmilAI (text/voice), take tests, and submit code.
- **Common (`/common/`)**: `Auth.tsx` (login), `Header.tsx`, `Footer.tsx`.

---

## 5. Core Data Models (Source of Truth)
*All relationships use `UUID`/text string primary keys.*

- `organizations`: `(id, name)`
- `users`: `(id, name, email, password, role, org_id)` (roles: student, teacher, admin).
- `subjects`: `(id, org_id, grade_band_id, name, teacher_id)`.
- `documents`: `(id, subject_id, org_id, name, content, type: [library|personal], chunk_count, uploaded_at)`.
- `chunks`: `(id, doc_id, org_id, subject_id, text, chunk_index)`.
- `chat_sessions`: `(id, user_id, subject_id, title)`.
- `chat_messages`: `(id, session_id, role: [user|assistant], content, citations)`.
- `assessments` & `questions`: Test structures tied to `subject_id`.
- `student_answers` & `submissions`: Tracks grades, code submissions, and teacher overrides.

> **CRITICAL RULE**: Every query involving documents, chunks, or chats MUST enforce tenant isolation using `WHERE org_id = ? AND subject_id = ?`.

---

## 6. AI Agent Engineering Guidelines
- **Sequential Execution**: Do not write placeholder functions or jump ahead. Solve one task perfectly, wait for user validation in the UI, then proceed.
- **No Over-Coding**: Stick exactly to the requested feature.
- **No Extraneous Imports**: If an AI capability is requested, rely exclusively on local `.venv` Python libraries (e.g., `sentence-transformers`, `llama-cpp-python`). No `openai` or `anthropic` imports.

---

## 7. AI Assistant Role & Persona
- **Your Role**: Senior AI Architect, System Mentor, and Guide.
- **Your Responsibility**: Do not act like a standard code-completion bot. You are advising on and building a sellable, enterprise-grade B2B platform for government and private schools. 
- **Your Standard**: Never produce quick "vibe code." Always prioritize scalable architecture (e.g., Staged Hybrid RAG, 1M+ PDF support), strict data tenant isolation, and clean offline-only code. You are here to help the user build an incredible, high-value product.
