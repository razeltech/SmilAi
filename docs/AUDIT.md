# SmilAI Comprehensive Project Audit

**Auditor:** Principal QA Engineer & Lead Software Architect  
**Version Audited:** v1.3.5 Release Candidate  
**Scope:** Recursive traversal of the entire repository (Frontend, Backend, Database, Configs, Tests).  

---

## PART 1 — Architecture Review

**1. Is the architecture modular?**
Yes. At a macro level, the backend is strictly divided into `rag`, `memory`, `learning_engine`, `assessment`, `voice`, and `documents`. This represents an excellent bounded-context approach.

**2. Are there circular dependencies?**
There are no *breaking* circular dependencies, but there is **Hidden Coupling**. Many services use inline imports inside functions (e.g., `app/rag/inference.py` importing `app.memory.service` inside `generate_rag_response_stream`) to avoid Python import errors on boot. This indicates that subsystems are mutually aware of each other rather than relying on an Event Bus or Dependency Injection.

**3. Which packages have become too large?**
`app/api/admin.py` is **593 lines long** (22KB). It has become a God-router. 

**4. Which responsibilities should be moved into separate services?**
`admin.py` must be split into:
- `api/subjects.py`
- `api/users.py`
- `api/assessments_admin.py`
- `api/documents_admin.py`

**5. Which files violate Separation of Concerns?**
`app/api/admin.py` violates SoC significantly by writing raw SQLite queries (e.g., `db.execute("SELECT ...")`) directly inside the API route handlers. 

**6. Does the project follow Clean Architecture principles?**
Mostly, but it fails at the Data Access Layer in the API tier. True Clean Architecture requires the API layer to call a Use Case / Service layer, which then calls a Repository layer for SQL. Currently, the API layer bypasses the Service layer and talks directly to the database in several files.

**7. Which components are tightly coupled?**
The `rag` package is tightly coupled to `Ollama`. If you wanted to swap to a different local inference engine (like vLLM or llama.cpp directly), you would have to rewrite `rag/inference.py`.

**8. Which components are reusable?**
The `learning_engine/` and `documents/ingestion.py` modules are highly reusable. The `learning_engine` relies on pure math and is completely decoupled from the LLM. 

**9. Are there hidden technical debts?**
* **Hardcoded Enums in SQL**: The `subjects` table limits `category` to exactly 5 values. 
* **Model Downloads on Startup**: `voice.py` uses `urllib.request.urlretrieve` to download Piper models if they don't exist.

---

## PART 2 — Educational Scalability

**Can it support ALL education levels without architectural redesign?**  
**No.** 

**What schema assumptions prevent it?**
1. `grade_bands`: The concept of a "grade band" maps well to K-12 (Primary, Secondary, CBSE). It maps poorly to higher education (BTech, MBBS, PhD) where progress is tracked by "Semesters", "Trimesters", or "Credit Hours".
2. `subjects.category`: In `schema.sql`, the category is hard-constrained to `CHECK(category IN ('GENERAL', 'PROGRAMMING', 'SCIENCE', 'LANGUAGE', 'MEDICAL'))`. This excludes Law, Commerce (CA/CS/BCom), Arts (BA), Engineering Core (Mechanical/Civil), and Vocational (ITI).

**What frontend assumptions prevent it?**
`types.ts` hardcodes `boardType?: 'ap_govt_ssc' | 'private_ssc' | 'private_cbse'`. This assumes the entire organization operates under a state/national board system, entirely breaking University or independent certification (CA/CMA) models.

**What backend assumptions prevent it?**
None explicitly outside of the schema validations mentioned above.

---

## PART 3 — Future AI Capability Audit

| Feature | Current Support | Future Readiness | Required Changes & Architectural Risk |
| :--- | :--- | :--- | :--- |
| **Regional Language** | None | **High** | Adapter Pattern (ADR-004) wraps the API layer. Low risk. |
| **Image Understanding** | None | **Low** | Requires Vision Language Models (VLM). `ingestion.py` currently strips out PDF images via PyMuPDF. High risk (requires multimodal ChromaDB schema). |
| **Drawing/Diagrams** | None | **Low** | Same as above. Needs Canvas UI and VLM processing. |
| **OCR / Handwriting** | None | **Medium** | Could be added to `documents/` as a pre-processing step (e.g. Tesseract) before embedding. Medium risk. |
| **Image/Diagram Gen** | None | **Medium** | Stable Diffusion local API could be integrated, but storing visual assets locally requires a File Storage schema update. |
| **Voice Cloning** | None | **Low** | Current models (Piper/Parler) use hardcoded presets. Requires speaker embedding capture. |
| **Streaming Voice** | None | **High** | Backend must be refactored from `FileResponse` to HTTP Chunked Transfer or WebSockets. Medium risk. |
| **Live Conversation** | None | **Medium** | Requires WebRTC or bidirectional WebSockets. High architectural effort. |
| **Video Understanding** | None | **Very Low** | Would require local FFmpeg frame extraction + VLM. Huge hardware spike. |
| **Multi-agent** | None | **Medium** | `inference.py` is single-turn. Needs a framework like LangGraph for orchestration. |
| **Knowledge Graph** | None | **Low** | Currently relies purely on Vector DB. Needs a Graph Database (Neo4j) to map complex curriculum dependencies. |

---

## PART 4 — Offline Readiness

**Is every subsystem offline-first?**  
**Yes, EXCEPT during initial bootstrapping.**

**Online Dependencies Found:**
1. `backend/src/python/app/api/voice.py` (Line 21): Downloads the Piper ONNX model from `https://huggingface.co/rhasspy/piper-voices/...` if the file is missing locally.
2. `backend/src/python/app/api/voice.py` (Line 70): `ParlerTTSForConditionalGeneration.from_pretrained(...)` will attempt to reach HuggingFace on first execution.

*No telemetry, crashlytics, or API keys were found in the frontend or backend.*

---

## PART 5 — Frontend Independence

**Could the backend support Flutter, Android, iOS, Unity without modifications?**  
**Yes.** 

The backend relies strictly on:
1. RESTful JSON endpoints.
2. Server-Sent Events (SSE) for chat streaming.
3. Standard JWT Bearer tokens (`api/auth.py`).
4. Standard Multipart Form Data for file uploads.

There are no session cookies, server-side rendered HTML, or React-specific hacks in the backend.

---

## PART 6 — Manual QA Checklist

### Core Setup & Infrastructure
- [ ] **Startup:** Delete `smilai.db` and start the server. Verify schemas auto-generate correctly.
- [ ] **Offline Mode:** Disconnect the host machine from Wi-Fi/Ethernet. Verify system boots without HuggingFace timeout crashes.
- [ ] **Profiles:** Boot using `--profile lite`. Verify Whisper Tiny and Piper load. Boot with `--profile pro`. Verify Whisper Large and Parler load.
- [ ] **Database Integrity:** Kill the server mid-chat. Restart. Verify the Write-Ahead Log recovers the transaction.

### User Management
- [ ] **Admin:** Create an Organization. Create Teacher, Create Student. 
- [ ] **Enrollment:** Enroll a student in a Subject. Unenroll them. Verify the Subject disappears from their Dashboard.

### Content & RAG
- [ ] **Documents:** Upload a 50-page PDF. Verify semantic chunking does not hang the UI.
- [ ] **Retrieval:** Ask a question specifically about page 42 of the uploaded PDF. Verify the exact chunk is cited in the UI.

### Assessment & Learning
- [ ] **Assessment Generation:** Generate a 10-question hard quiz. Verify questions map to syllabus chunks.
- [ ] **Assignments:** Submit a code/text file as a student. 
- [ ] **Learning Engine:** Grade the submission. Verify the student's `concept_mastery` updates accurately using the 0.6 deterministic weight.

### AI Engine (Chat & Voice)
- [ ] **Memory:** Say "I struggle with fractions." Wait 10 seconds. Check SQLite `student_memory` table. Verify trait extracted.
- [ ] **Voice:** Turn on Voice mode. Ask a question containing the equation `E=mc^2`. Verify TTS reads it naturally and does not crash on the `$`.
- [ ] **Performance Load:** Send 50 rapid-fire chat messages. Monitor RAM to ensure Ollama does not memory leak and Chroma handles concurrent reads.

---

## PART 7 — Release Readiness

**1. Is SmilAI production ready?**
Yes, but only for early-adopter pilot schools (Beta phase). The architectural boundaries are incredibly strong, but the bootstrapping edge cases need polish.

**2. What blocks deployment?**
The automatic HuggingFace downloads in `voice.py`. In a truly offline rural school, the server will crash on first run because it cannot reach the internet to fetch Piper/Parler. The models must be pre-bundled in the deployment payload.

**3. What should be completed before v1.4 (Translation)?**
* Refactor `app/api/admin.py` into smaller, decoupled routers.
* Remove inline SQL from API routers and move it into the Services layer.
* Fix the hardcoded HuggingFace dependencies.

**4. What should wait until v2.0?**
Schema rewrites to support Higher Education (Degrees, Semesters, generic Categories), Knowledge Graphs, and Vision Language Models.

**5. Architecture Score:**
**8.5 / 10**  
*(Deductions for God-routers and inline SQL, but immense praise for modularity, deterministic engines, and deployment profiling).*
