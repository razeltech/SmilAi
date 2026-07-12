# SmilAI — Phase Execution Plan

**Purpose of this document:** Gemini (or any AI builder) hallucinates most when given
a big goal and freedom to fill in the gaps. This document removes the gaps. Each
phase has a fixed, small deliverable list, an explicit "done when" test, and an
explicit **stop list** of things it must NOT build yet, even if it thinks it's a
natural next step.

**How to use this with Gemini AI Studio (or any builder):**
1. Every session, give it — in this order — `rules.md`, `SmilAI_PRD.md`,
   `SmilAI_SRS.md`, and this file.
2. Tell it explicitly: *"We are on Phase X. Do only what Phase X lists. If you think
   something from a later phase is needed, stop and say so instead of building it."*
3. At the end of a session, run the phase's **Done-when checklist** yourself before
   telling it to move to the next phase. Do not let it self-certify.
4. If it invents a field, endpoint, or file not named in the SRS/this plan, that's the
   signature of hallucination — stop it, point at the SRS section, and ask it to
   redo just that piece.

---

## Phase 0 — Audit what already exists (do this before anything else)

Gemini has already built login and a dashboard. Before adding anything, verify what
exists actually matches the spec — bolting new phases onto a shaky foundation is how
small hallucinations become big rework later.

**Audit checklist (go through each with Gemini, fixing gaps before moving on):**

- [ ] Does login issue a real JWT (or session) containing **role** (`student` /
      `teacher` / `admin`) and **org_id**? (FR-ACC-4) If it's a stubbed/fake login,
      flag it now — this product needs real auth from day one, unlike a throwaway demo.
- [ ] Are passwords hashed (bcrypt/argon2), not stored or compared in plaintext?
- [ ] Does the dashboard already assume a role, or is it one generic view? It needs to
      eventually branch by role — check what exists so you know what to adapt vs.
      rebuild.
- [ ] Is there any subject/course concept yet, or is the dashboard subject-agnostic?
      (There should be none yet if only login+dashboard were built — confirm this.)
- [ ] Is the server reachable from another device on the LAN (not just
      `localhost`), or is it currently bound to loopback only? (NFR-1a) If it's
      localhost-only, this needs fixing now, before more is built on top.
- [ ] Is anything calling an external/cloud API (even accidentally, e.g. a UI library
      pulling fonts/icons from a CDN)? Confirm zero network calls at runtime. (NFR-1)

**Done when:** you have a written list of what matches spec, what needs fixing, and
what needs to be added — before Phase 1 tasks begin. Fix gaps found here first.

---

## Phase 1 — Foundation

**Goal:** one working subject, one grade band, one teacher, real accounts, basic
cited chat. This is the smallest version of the whole loop working end to end.

**Build exactly this:**
- [ ] `Organization`, `User` (role + org_id), `GradeBand`, `Subject` (org_id,
      grade_band_id, owning teacher_id), `Enrollment` — per SRS §6 data model.
- [ ] Admin can create ONE grade band and ONE subject, and assign ONE teacher.
      (Decide together which of the six — English, Telugu, Hindi, Maths, Science,
      Social Studies — is the pilot before starting this task.)
- [ ] Student signup/enrollment into that one subject only.
- [ ] Document ingestion: teacher can upload `.txt`/`.md`/`.html` into the subject's
      knowledge base (FR-ING-1). Parser registry pattern per SRS §3.2 — one parser
      class per format, nothing hardcoded per subject.
- [ ] Chunking with configurable size/overlap (FR-ING-5).
- [ ] Local embeddings + local vector store, chunks tagged with `org_id` +
      `subject_id`.
- [ ] `/v1/chat` — student asks a question, gets a **cited** streamed (SSE) answer
      from that subject's knowledge only (FR-CHAT-1, FR-CHAT-3).
- [ ] Persona layer: one shared system prompt/persona definition injected into every
      LLM call, even at this early stage (FR-PERSONA-1) — do not let Gemini write
      ad hoc prompts per feature; there is one persona module every feature calls.

**Explicitly do NOT build in Phase 1 (stop list):**
- A second subject or grade band.
- Voice (STT/TTS) — text only for now.
- Test generation, code grading, or student records — Phase 3/4.
- Any teacher-override UI beyond basic document upload.

**Done when:** a teacher logs in, creates/uploads material for the one pilot subject;
a student logs in, asks a question, gets a correct cited answer, streamed. Test this
yourself, on a second device over the LAN, not just localhost.

---

## Phase 2 — Voice

**Goal:** the same chat, now speakable and listenable, for any subject built so far.

**Build exactly this:**
- [ ] `/v1/voice/transcribe` — faster-whisper, local (FR-VOICE-1).
- [ ] Transcript shown to student, editable, before it's sent as a question
      (FR-VOICE-2) — do not auto-submit without letting the student see/fix it.
- [ ] `/v1/voice/speak` — two-tier: Indic Parler-TTS primary, Piper fallback
      (FR-VOICE-4). Build the fallback logic explicitly — do not treat Piper as an
      afterthought bolted on later; it's part of this phase's definition of done.
- [ ] Mic button in composer, speaker icon on any assistant message (FR-VOICE-3) —
      speech is on-demand, never forced automatically.
- [ ] **Benchmark real VRAM usage** on the actual RTX 3060 with LLM + Whisper + TTS
      loaded together. Do this before writing any concurrency/queueing code — the
      numbers in SRS §5 are estimates to verify, not facts to build against blindly.

**Explicitly do NOT build in Phase 2 (stop list):**
- Telugu/Hindi voice (FR-LANG-2) — English voice only.
- Any subject beyond the Phase 1 pilot.
- Assessment generation or code grading.

**Done when:** a student can speak a question, see the transcript, get a spoken
answer back; forcing the GPU busy (e.g. run two requests at once) correctly falls
back to Piper instead of erroring or hanging.

---

## Phase 3 — Assessment engine (test generation + answer verification)

**Goal:** the pilot subject's virtual teacher can generate a test and grade answers.

**Build exactly this:**
- [ ] `Assessment`, `Question`, `StudentAnswer`, `AnswerEvaluation` entities (SRS §6).
- [ ] `/v1/subjects/{id}/assessments` — generate a test from that subject's ingested
      material, with configurable question count/topic/difficulty (FR-ASSESS-1).
      Every generated question must reference its source chunk(s) — if Gemini
      generates a question with no traceable source, that's a hallucination signal;
      reject it.
- [ ] At least MCQ and short-answer question types (FR-ASSESS-2) for this phase;
      numeric/derivation/code question types can follow once these two work.
- [ ] Answer verification: MCQ graded deterministically; short-answer graded by LLM
      against a rubric, returning score **and** an explanation (FR-ASSESS-3).
- [ ] `StudentSubjectRecord` — test results feed into a per-subject record
      (FR-RECORD-1).
- [ ] Teacher can view and override any generated question or graded answer
      (FR-ASSESS-4).

**Explicitly do NOT build in Phase 3 (stop list):**
- A second subject.
- Code-writing questions or code grading — Phase 4.
- Numeric/derivation question types unless MCQ + short-answer are solid first.

**Done when:** a teacher generates a test from real ingested material, a student
takes it, and both objective and subjective answers come back graded with a clear
explanation, visible in that student's subject record.

---

## Phase 4 — Code grading (confirm scope first)

**Before starting: confirm whether Computer Science/coding is a 7th v1 subject or
deferred** (this was left open in SRS §9 — settle it before Gemini builds anything
here, since it changes whether this phase happens now or much later).

**If confirmed in scope, build exactly this:**
- [ ] Student can upload a code file or project (zip/folder) tied to an assignment
      (FR-GRADE-1).
- [ ] **Static analysis only** — reading the code for logic/structure/style/bug
      patterns. **Do not execute the uploaded code.** If Gemini suggests running
      `exec`/`subprocess`/a sandbox "to check if it works," stop it — that's Phase 8,
      security-reviewed separately (FR-GRADE-2, rules.md non-negotiables).
- [ ] Rubric-driven scoring (FR-GRADE-3), feedback through the persona layer, not a
      raw linter dump (FR-GRADE-4).
- [ ] Teacher can view/override grades (FR-GRADE-5); submissions/grades persist
      (FR-GRADE-6).

**Done when:** a student submits code, gets a rubric-based score and specific,
persona-toned corrections without any code execution happening anywhere in the path.

---

## Phase 5 — Generalize the subject framework (the gate)

**Goal:** prove a second subject needs *configuration only*, not new code. This is
the single most important checkpoint in the whole plan.

**Build exactly this:**
- [ ] Stand up a **second** subject from the confirmed catalog (English, Telugu,
      Hindi, Maths, Science, Social Studies — whichever wasn't the pilot) using only:
      new `Subject`/`VirtualTeacherConfig` rows, new ingested documents, a rubric.
- [ ] Explicitly verify **zero new code files or subject-specific `if` branches**
      were needed in shared modules (chat, assessment, grading, persona). If Gemini
      had to write subject-specific logic anywhere outside config/data, the framework
      isn't generalized yet — fix that before adding more subjects, don't route
      around it.
- [ ] Confirm subject-based records stay isolated (FR-RECORD-2) — the second
      subject's teacher cannot see the first subject's student data.

**Explicitly do NOT build in Phase 5 (stop list):**
- Subjects 3–6 — prove it with exactly two before scaling further.
- Anything from Phase 6/7/8.

**Done when:** the second subject works at the same quality as the first, and you
can point to the specific config/data rows that made it possible — no new code.

---

## Phase 6 — Library-scale ingestion + OCR

- [ ] Bulk ingestion endpoint accepting many files in one job (FR-ING-1, at scale).
- [ ] OCR pipeline for scanned PDF pages → text before normal chunking (FR-ING-4);
      low-confidence pages flagged for teacher review, not silently ingested.
- [ ] Chunking tuned for textbook structure (chapter/section awareness), configurable
      per content type (FR-ING-5).

**Done when:** a teacher bulk-ingests a real scanned textbook in one job, and its
content is retrievable with citations, with any low-quality OCR pages flagged.

---

## Phase 7 — Regional interaction languages (voice)

- [ ] Add Telugu and Hindi **voice** (STT + TTS) via the pluggable adapter interface
      already designed for this (FR-LANG-2) — this should be an adapter addition, not
      an orchestration rewrite, if Phase 2 was built correctly.

**Done when:** a student can speak to SmilAI in Telugu or Hindi and get a spoken
response, for any subject already configured.

---

## Phase 8 — Sandboxed execution grading

- [ ] Security-reviewed subsystem for running student code against test cases:
      resource limits, no network access, timeouts, filesystem isolation.
- [ ] This is new, isolated infrastructure — do not let it leak execution
      capability into the Phase 4 static-analysis path.

**Done when:** code can be safely executed against test cases with hard resource/time
limits and no access beyond the sandbox, reviewed specifically for security before
any student-facing rollout.

---

## Phase 9+ (not committed — do not start without a fresh planning pass)

Remaining subjects beyond the confirmed six · professional domains (engineering,
medicine, CA, law) · Tamil voice · plagiarism detection · teacher/admin analytics
dashboards · mobile front end · multi-GPU scaling · any multi-institution hosting.

---

## Anti-hallucination checklist (apply at every phase)

- Does every new field/entity trace back to SRS §6? If Gemini invents one, check the
  SRS before accepting it — either add it there deliberately, or reject it.
- Does every new endpoint match the SRS §7 API sketch, or is it a deliberate,
  documented extension? Undocumented new endpoints are a hallucination flag.
- Is anything calling out to the internet? Grep for `http://`/`https://` to external
  domains, npm/pip packages that phone home, or "helpful" CDN includes.
- Is a "later phase" item (see each phase's stop list) being built early because it
  seemed convenient? Stop and confirm before continuing.
- Can you point to the exact FR-ID or PRD section that justifies what was just built?
  If not, it's speculative — verify before it's considered done.
