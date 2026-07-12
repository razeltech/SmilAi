# SmilAI — Software Requirements Specification (SRS)

**Status:** Draft v1 · Companion to `SmilAI_PRD.md` · Read the PRD first for the "why."

---

## 1. Purpose and scope

This document specifies the technical requirements for SmilAI v1: an on-premise,
fully offline virtual-teacher platform providing (a) RAG-based conversational Q&A over
subject material, (b) voice interaction (Indian-accented English STT/TTS), (c) test
paper generation and answer verification, and (d) static code grading — all as
**configurations of one shared brain**, assigned by an admin to subjects and grade
bands the same way a school assigns teachers. It is written to be buildable phase by
phase (see PRD §9) without deviation into out-of-scope features — specifically,
without building for every subject and grade band before the core loop is proven on
one.

**Hard constraint carried over from prior work and still true here:** fully local —
no API keys, no cloud inference, no runtime network dependency. Target hardware for
v1: one RTX 3060 12GB GPU per institution server.

---

## 2. System overview

```
                         Client Layer
   Web UI (chat + mic/speaker) | future: mobile, LMS plugin, kiosk
--------------------------------------------------------------------
                    REST / WebSocket / SSE
--------------------------------------------------------------------
                       API Gateway (/v1)
   Auth (JWT) · Org/Role routing · Rate limiting · Request logging
--------------------------------------------------------------------
                   Orchestration Layer
   Conversation Manager · Prompt Builder · Persona Layer
   Voice Pipeline Controller (STT -> LLM -> TTS)
   Grading Pipeline Controller (parse -> analyze -> score -> feedback)
--------------------------------------------------------------------
        Knowledge Layer              Grading Layer
   Hybrid/Vector Search           Static Code Analyzer
   Reranker (later)               Rubric Engine
--------------------------------------------------------------------
                     AI Services (GPU-aware)
   Local LLM (chat + grading reasoning)
   Embedding model
   STT: faster-whisper
   TTS: Indic Parler-TTS (primary) + Piper (fallback)
   OCR engine
--------------------------------------------------------------------
                       Storage Layer
   PostgreSQL (accounts, orgs, courses, submissions, grades, logs)
   Vector store (per-org/course knowledge, metadata-filtered)
   File storage (uploads, audio, generated speech)
--------------------------------------------------------------------
```

Every box in **AI Services** sits behind an adapter interface (mirroring the pattern
already proven in Project Athena). New models, or a second GPU later, must not require
changing any layer above the adapter.

---

## 3. Functional requirements

Numbered `FR-<area>-<n>`. Each must have a test before being marked done.

### 3.1 Accounts & organizations
- **FR-ACC-1:** System supports roles: `student`, `teacher`, `admin`, scoped to one
  `organization` (the institution).
- **FR-ACC-2:** All data (documents, submissions, grades, chat history) is tagged with
  `org_id`; queries never cross org boundaries.
- **FR-ACC-3:** Teachers can create/manage `courses` within their org; students are
  enrolled in courses.
- **FR-ACC-4:** Real authentication (hashed passwords, JWT with role + org claims) —
  no dev-stub login in this product, since real student accounts are core to v1.

### 3.2 Knowledge ingestion (RAG)
- **FR-ING-1:** Teachers can bulk-ingest documents (textbooks, notes) into a
  **course-level, persistent knowledge base** ("library mode") — a single ingestion
  job may accept many files at once.
- **FR-ING-2:** Students may optionally ingest their own supplementary material into a
  personal scope, kept separate from course-wide library content.
- **FR-ING-3:** Supported input formats at launch: `.txt`, `.md`, `.html`; `.docx` and
  `.pdf` (including OCR'd scanned PDFs) added per the phased parser rollout (same
  extensibility pattern as Athena: one parser class per format, registered centrally).
- **FR-ING-4:** OCR pipeline converts scanned/imaged PDF pages to text before normal
  chunking; must flag pages where OCR confidence is low for teacher review rather than
  silently ingesting garbled text.
- **FR-ING-5:** Chunking must preserve enough structure for textbook-style content
  (chapter/section boundaries where detectable) — not just fixed word-count windows —
  so retrieved passages make sense on their own. Track chunk size/overlap as configurable,
  tunable per content type (chat notes vs. textbook chapters).

### 3.3 Conversational Q&A
- **FR-CHAT-1:** Student asks a question (text or voice-transcribed); system retrieves
  from the course's knowledge base (library + any personal scope) and answers with
  citations, per the RAG pattern already validated in Athena.
- **FR-CHAT-2:** Multi-turn conversation history is maintained per session.
- **FR-CHAT-3:** Answers are streamed token-by-token to the client (SSE), matching
  Athena's approach, for both text and voice-derived responses.
- **FR-CHAT-4:** All chat responses pass through the **Persona Layer** (see §3.6) before
  reaching the client, so tone is consistent regardless of source module.

### 3.4 Voice pipeline
- **FR-VOICE-1:** Student can record via mic in the composer UI; audio is sent to the
  API and transcribed locally via **faster-whisper**.
- **FR-VOICE-2:** Transcript is shown to the student (editable) before submission as a
  question, so STT errors can be caught.
- **FR-VOICE-3:** Any assistant text response can be converted to speech on demand
  (speaker icon), not forced automatically — avoids unnecessary GPU load.
- **FR-VOICE-4:** TTS is **two-tier**: primary is **Indic Parler-TTS** (GPU-preferred,
  Indian-accented, persona-matched voice); if GPU is unavailable/busy/over budget,
  fall back to **Piper** (CPU-capable, gender-only voice selection, lower quality).
  The fallback decision is automatic and logged, not user-facing as an error.
- **FR-VOICE-5:** Voice pipeline (STT → LLM → TTS) must not block other users'
  text-only requests indefinitely — see GPU orchestration, §5.

### 3.5 Subject and virtual-teacher assignment
- **FR-SUBJ-1:** Admin can create a `Subject` scoped to a `GradeBand`/`Class` within
  their org, and assign one real `Teacher` account to own it.
- **FR-SUBJ-2:** Each `Subject` has exactly one active **virtual teacher instance** —
  a configuration (knowledge base scope, rubric defaults, test defaults) layered on
  top of the shared persona engine (§3.9). Creating a new subject must be a
  **configuration action**, not a code change (this is the platform's central
  extensibility requirement — see NFR-5a).
- **FR-SUBJ-3:** A student is enrolled per-subject (not globally) — their access,
  knowledge base, and records are scoped to the subjects they're enrolled in.
- **FR-SUBJ-4:** The owning real teacher can view/edit their subject's knowledge base,
  rubric, and test settings, and can review every student interaction and grade within
  their subject.

### 3.6 Subject-based student records
- **FR-RECORD-1:** Every student has a record **per subject**: test scores over time,
  code-grading history (where applicable), topics/questions they've struggled with.
- **FR-RECORD-2:** Records from different subjects are never merged or cross-visible
  to a different subject's teacher — a Math teacher does not see a student's Coding
  record.
- **FR-RECORD-3:** Both the student and their subject's real teacher can view the
  record; admin can view aggregate (not necessarily per-answer) statistics across
  subjects for their org.

### 3.7 Test/assessment generation and answer verification
- **FR-ASSESS-1:** The virtual teacher can **generate a test paper** from the
  subject's ingested material: configurable question count, topic coverage, and
  difficulty. Generated questions must be traceable back to source material (same
  citation discipline as chat answers) so a teacher can audit where a question came
  from.
- **FR-ASSESS-2:** Supports multiple question types at minimum: multiple-choice,
  short-answer, and (for applicable subjects) numeric/derivation and code-writing
  questions.
- **FR-ASSESS-3:** **Answer verification** — objective question types (MCQ, numeric
  with exact/tolerance match) are graded deterministically; subjective types
  (short-answer, essay, derivation, code) are graded by the LLM against a
  teacher-defined or default rubric, returning a score **and an explanation** of the
  grading, in persona tone.
- **FR-ASSESS-4:** The owning teacher can review and override any auto-generated test
  question or any auto-graded answer before or after it reaches a student.
- **FR-ASSESS-5:** A generated test and its grading results feed directly into the
  subject-based student record (FR-RECORD-1).

### 3.8 Code grading
- **FR-GRADE-1:** Student uploads a single code file or a project (zip/folder) tied to
  a specific course assignment.
- **FR-GRADE-2:** System parses the submission's structure (files, languages present)
  and runs **static analysis**: correctness-by-reading, common bug patterns, style,
  structure — v1 does **not** execute the code (see PRD §6, roadmap P7 for sandboxed
  execution).
- **FR-GRADE-3:** Grading is **rubric-driven** — a teacher-defined or default rubric
  (per assignment or per course) maps analysis findings to a numeric score plus
  qualitative feedback.
- **FR-GRADE-4:** Feedback is returned in SmilAI's persona voice/tone (not a raw
  linter dump) — specific, actionable, encouraging, with clear "what to fix and why."
- **FR-GRADE-5:** Teachers can view all submissions/grades for their course and
  override any grade.
- **FR-GRADE-6:** A submission and its grade are stored (not just returned
  transiently) so a student's progress over time is queryable.

### 3.9 Persona layer
- **FR-PERSONA-1:** A single system-level persona definition (name, tone, style rules)
  is injected into every LLM call across chat and grading, so behavior is consistent
  across modules.
- **FR-PERSONA-2:** Persona content (name, voice, described personality) must be
  original — not a reproduction of any existing copyrighted/trademarked fictional
  character.
- **FR-PERSONA-3:** Voice output uses one consistent persona-matched voice profile in
  Indic Parler-TTS (not a random/generic voice per request).

### 3.10 Multilingual — two distinct concerns, do not conflate

- **FR-LANG-1 (Subject content — v1, not deferred):** Telugu and Hindi are **taught
  subjects** in the v1 catalog (alongside English, Maths, Science, Social Studies).
  Ingestion, chunking, test generation, and answer verification must work correctly
  on **Telugu- and Hindi-script content** from day one for those two subjects — this
  is not the same requirement as voice support and should not be scheduled as if it
  were a later phase.
- **FR-LANG-2 (Interaction language — later phase):** A student *speaking to SmilAI*
  in Telugu or Hindi (rather than English) is a separate, deferred capability. STT/TTS
  adapters must be **language-pluggable** so Telugu, Hindi (and later Tamil) voice
  models can be added without changing the orchestration layer — design the adapter
  interface for this now even though only English voice interaction ships in v1. A
  student can study the Telugu *subject* through English-medium interaction before
  Telugu *voice* support exists.

---

## 4. Non-functional requirements

- **NFR-1 (Offline, permanent):** No component may require internet access at
  runtime, **at any phase of the roadmap, permanently**. All models run on-premise.
  **No paid API of any kind is ever used**, including in future phases; if a feature
  seems to need one, the correct answer is a local alternative or "not built yet,"
  never an API key. (Model *downloads* during initial installation are fine; runtime
  operation must not depend on connectivity.)
- **NFR-1a (LAN-served, multi-device):** The server must serve **many concurrent
  devices over the institution's local network** (a full lab or classroom), not a
  single local user — this shapes concurrency (§5) and API/CORS configuration (must
  accept requests from LAN client IPs, not just localhost/loopback).
- **NFR-2 (Data privacy):** Student submissions, voice recordings, and chat history
  never leave the institution's LAN.
- **NFR-3 (Performance targets — confirm with pilot before Phase 3 sign-off):**
  - Text chat: first token within ~2s under normal load.
  - Voice round-trip (speak → hear answer): a target should be set once the two-tier
    TTS is benchmarked on the actual 3060 — do not assume a number before measuring.
- **NFR-4 (Concurrency):** System must degrade gracefully (queue, not crash) when
  multiple students use voice or grading simultaneously on a single-GPU box — see §5.
- **NFR-5 (Extensibility):** Every model-facing component (LLM, embedder, vector
  store, STT, TTS, OCR, parsers) sits behind an interface with a single current
  implementation, following the adapter pattern already validated in Project Athena.
  A new model or a second GPU must be addable by adding an adapter, not editing
  callers.
- **NFR-5a (Subject extensibility):** Adding a new subject or grade band must be a
  **data/configuration action** (new `Subject` + `VirtualTeacherConfig` rows, new
  ingested documents, a rubric) — never a code change. This is the platform's central
  bet and the specific thing Phase 5 (PRD §9) exists to validate before scaling
  subject count.
- **NFR-6 (Auditability):** Every grade issued, and every persona-layer response, is
  logged with enough context (submission id, rubric version, model/version used) to
  explain later why a particular score was given.

---

## 5. GPU resource strategy (single RTX 3060 12GB)

This is the highest-risk technical area and should be validated empirically in Phase
1/2, not assumed. Rough, **unverified** VRAM budgeting to plan around (measure on
real hardware before committing):

| Component | Rough VRAM (approx., to verify) |
|---|---|
| Local LLM (7B, Q4) | ~5 GB |
| Local LLM (14B, Q4) | ~9 GB |
| Embedding model | small, <1 GB |
| faster-whisper (small/medium) | ~1–2 GB |
| Indic Parler-TTS | GPU-preferred; size TBD — benchmark before assuming it fits alongside a 14B LLM |

**Implication:** on a single 12GB card, running a 14B LLM *and* GPU-based TTS *and*
Whisper concurrently may not fit. Recommended approach for v1:

- **Serialize GPU-heavy stages per request** (STT → LLM → TTS run in sequence, not
  in parallel, per request) rather than holding all models resident at full load
  simultaneously if VRAM is tight.
- **Load/unload discipline or a model-serving queue** so concurrent users' voice
  requests don't collide and OOM the GPU — a simple request queue for GPU-bound work
  is acceptable for v1; true multi-user parallel voice at scale is a later hardware
  (multi-GPU) problem, flagged in PRD roadmap as P8+.
- Default to the **7B LLM** if voice + grading + chat all need to run concurrently on
  one card; reserve 14B for lighter concurrent load or a future second GPU.
- **Piper fallback exists exactly for this**: when the GPU is already committed
  (e.g., mid-inference for another user), TTS requests can fall back to CPU-based
  Piper rather than queuing indefinitely.

This section should be revisited with real benchmarks as the first empirical task of
Phase 2 (voice), before committing to specific concurrency limits in the product.

---

## 6. Data model (core entities)

- **Organization** — the institution.
- **User** — id, role (`student`/`teacher`/`admin`), org_id.
- **GradeBand** — id, org_id, label (e.g., "Class 8", "Engineering Year 2").
- **Subject** — id, org_id, grade_band_id, owning `teacher` user_id, active virtual
  teacher config reference.
- **VirtualTeacherConfig** — id, subject_id, knowledge base scope, rubric defaults,
  test-generation defaults — layered on the shared persona engine, not a separate
  model per subject.
- **Enrollment** — user_id (student), subject_id — students are enrolled per subject,
  not globally.
- **KnowledgeDocument** — id, subject_id, org_id, source, ingestion type
  (`library` | `personal`), chunk_count.
- **Chunk** — id, doc_id, org_id, subject_id, source, chunk_index, text.
- **ChatSession** — id, user_id, subject_id, message history.
- **Assignment** — id, subject_id, rubric reference (code-grading assignments).
- **Rubric** — id, subject_id or assignment_id, criteria + weighting, default vs.
  teacher-customized.
- **Submission** — id, assignment_id, student_id, files/paths, submitted_at.
- **GradeResult** — id, submission_id, score, per-criterion breakdown, feedback text,
  rubric_version, model/version used, teacher_override (nullable).
- **Assessment** — id, subject_id, generated_by (virtual teacher / teacher-authored),
  question_count, topic_coverage, difficulty, created_at.
- **Question** — id, assessment_id, type (`mcq`|`short_answer`|`numeric`|`derivation`|
  `code`), prompt, source_chunk_ids (for auditability), correct_answer/rubric ref.
- **StudentAnswer** — id, question_id, student_id, answer_content, submitted_at.
- **AnswerEvaluation** — id, student_answer_id, score, explanation, graded_by
  (`deterministic`|`llm_rubric`), teacher_override (nullable).
- **StudentSubjectRecord** — id, student_id, subject_id — an aggregating view over a
  student's Assessments/GradeResults within that one subject; never merges across
  subjects (FR-RECORD-2).
- **VoiceArtifact** — id, related chat message id, audio file reference, direction
  (input transcript / output speech), engine used (Indic Parler-TTS | Piper).

---

## 7. External interface — API sketch (`/v1`, versioned, stable for future clients)

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/auth/login` | Real login, returns JWT with role + org_id |
| POST | `/v1/grade-bands` | Admin creates a grade band/class |
| POST | `/v1/subjects` | Admin creates a subject, assigns owning teacher |
| POST | `/v1/subjects/{id}/enrollments` | Enroll a student in a subject |
| POST | `/v1/subjects/{id}/documents/bulk` | Teacher bulk library ingestion |
| POST | `/v1/documents` | Student personal-scope ingestion |
| POST | `/v1/chat` | Text or voice-derived question → streamed, cited answer (SSE), scoped to a subject |
| POST | `/v1/voice/transcribe` | Audio in → transcript (faster-whisper) |
| POST | `/v1/voice/speak` | Text in → audio out (Indic Parler-TTS or Piper) |
| POST | `/v1/subjects/{id}/assessments` | Generate a test paper for a subject |
| GET | `/v1/assessments/{id}` | Retrieve a generated assessment (questions) |
| POST | `/v1/assessments/{id}/answers` | Student submits answers |
| GET | `/v1/assessments/{id}/results` | Retrieve graded results |
| PUT | `/v1/answers/{id}/evaluation` | Teacher overrides an answer's grade |
| POST | `/v1/assignments/{id}/submissions` | Student uploads code/project |
| GET | `/v1/submissions/{id}/grade` | Retrieve code grading result |
| PUT | `/v1/submissions/{id}/grade` | Teacher overrides a code grade |
| GET | `/v1/students/{id}/subjects/{subject_id}/record` | Subject-scoped student record |
| GET | `/v1/health` | Health check |

This list should be extended, not restructured, as features are added — front ends
(web, mobile, LMS plugin) all depend on this contract remaining stable.

---

## 8. Security & integrity considerations

- Password hashing (e.g., bcrypt/argon2) — no plaintext, no dev-stub auth in this
  product (unlike Athena's early dev shortcut).
- File upload validation: size limits, allowed extensions, virus/malware scanning
  consideration for code uploads before parsing.
- **Code grading in v1 does not execute student code** — this removes the biggest
  security risk (arbitrary code execution) from the current scope by design. When
  Phase 7 (sandboxed execution) is built, it requires its own security review:
  resource limits, no network access, timeouts, filesystem isolation.
- Voice recordings and submissions are institution data — storage location, retention
  period, and deletion policy must be defined (see PRD open questions).

---

## 9. Constraints & assumptions

- **v1 subject catalog is fixed and concrete:** English, Telugu, Hindi, Mathematics,
  Science, Social Studies. Pilot one, prove the loop, then configure the rest in
  (Phase 5 gate). Computer-science/coding is currently assumed to remain part of v1
  scope because code grading (§3.8) is already fully specified — **confirm this
  explicitly**: is programming a 7th v1 subject, or deferred alongside the
  professional domains (engineering/medicine/CA/law)? This changes what "Phase 4 —
  code grading" means in the roadmap.
- Single RTX 3060 12GB per institution for v1; architecture must not assume more GPU
  is always available, but must not preclude scaling to more later (NFR-5).
- **No internet at runtime, ever, permanently** — not in v1, not in any future phase.
  Initial model downloads happen once during installation only. No paid API of any
  kind is ever called (NFR-1).
- **LAN-served, multi-device from day one** (NFR-1a) — this is not a single-user
  desktop app; design the server/API/CORS layer for a lab full of simultaneous
  devices from Phase 1, not retrofitted later.
- English voice interaction ships first; Telugu/Hindi **voice** interaction is a
  defined but deferred phase (FR-LANG-2). Telugu/Hindi **subject content** is not
  deferred — it's in the v1 catalog (FR-LANG-1).
- Static analysis only for code grading in v1; sandboxed execution is explicitly
  deferred and separately scoped.

---

## 10. Acceptance criteria (per phase, high level)

- **P1 done when:** admin can create one grade band, one subject, assign a teacher;
  a teacher and student account can log in; a student can ask a question against
  teacher-ingested subject material and get a cited answer.
- **P2 done when:** a student can speak a question via mic, see the transcript, get an
  answer, and play it back in SmilAI's voice; Piper fallback triggers correctly when
  forced (e.g., GPU busy).
- **P3 done when:** a virtual teacher can generate a test paper from ingested material,
  a student can answer it, and both objective and subjective answers are graded with
  an explanation, feeding a per-subject student record.
- **P4 done when:** a student can submit code for a defined assignment and receive a
  rubric-based score and specific corrections in persona voice/tone; a teacher can view
  and override it.
- **P5 done when:** a second subject (and ideally a second grade band) has been stood
  up using only configuration (no new code) and produces the same quality of
  teaching/testing/grading as the first — this is the gate before adding more subjects.
- **P6 done when:** a teacher can bulk-ingest a full textbook in one job, and scanned
  PDF pages are OCR'd and retrievable with citations.

---

## 11. Open decisions (carry into a living decision log once building starts)

- Rubric structure: fixed-per-subject vs. teacher-editable per assignment/assessment
  (PRD open question — affects the `Rubric` entity design).
- Minimum supported hardware if an institution has less than a 3060 (CPU-only degraded
  mode vs. hard minimum spec).
- Data retention policy for submissions/voice recordings/test answers.
- Exact VRAM budget and concurrency limits — must be set from real benchmarks (§5),
  not assumed.
- Which subject and grade band to pilot first (recommend deciding this before Phase 1
  starts, since P1's acceptance criteria depend on it).
- How much a subjective-answer LLM grade should be trusted vs. always routed to the
  teacher for confirmation early on, while grading quality is still being validated.
