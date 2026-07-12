# SmilAI — Product Requirements Document (PRD)

**Status:** Draft v1 · **Owner:** [you] · **Codename:** SmilAI (working name)

---

## 1. Vision

SmilAI is a **fully offline virtual AI teacher platform** for schools, colleges, and
professional exam prep: an installed, on-premise system where every student has a
subject teacher they can talk to without fear or hesitation — ask the "silly"
question, get it wrong, try again, with total patience — through a warm, human-like
persona, in Indian-accented English first, with Telugu/Tamil/Hindi to follow.

The core insight driving this product: **many students don't ask questions in class
out of fear or shyness.** SmilAI exists to remove that barrier — a virtual teacher who
is infinitely patient, available any time, and never makes a student feel judged for
not knowing something.

It is **not** a single chatbot with a code-grading feature bolted on. It is a
**platform where an institution's admin staffs subjects with virtual teachers** —
much like assigning a real teacher to a real subject — and each virtual teacher then:
teaches (conversational Q&A over that subject's material), **sets and grades tests**
(generates test papers from the ingested syllabus, verifies student answers), and
tracks each student's progress in that subject over time. Coding, mathematics,
science, medicine, CA, law — every subject is a **configuration of the same underlying
brain**, not a separate build.

It is an installable product: an institution buys a server, we install SmilAI's brain
and models on it, and give them a front end. The **API is the actual product** — the
same "AI brain, swappable face" principle as Project Athena.

**Two constraints are permanent architectural law, not v1-only decisions:**

1. **No paid API of any kind, at any phase, ever.** Every model — LLM, embeddings,
   STT, TTS, OCR — runs on the institution's own hardware. No API keys, no
   pay-per-use cloud calls, under any circumstance, now or in any future phase.
2. **LAN-first, fully offline.** The server runs inside the institution's own local
   network (a computer lab, a school's server room) and serves **many student/teacher
   devices on that LAN simultaneously** — not just one browser talking to one machine.
   No internet connection is required for the system to function at all, ever.

---

## 2. Problem statement

- Students need fast, patient, always-available help understanding course material and
  getting feedback on code — teachers can't review every submission in depth.
- Institutions in many regions want AI tools that work **without sending student data to
  the cloud** and without recurring API costs.
- Existing AI coding/study assistants are text-only, English-only, and don't feel
  personal — a voice-driven, locally-hosted, Indian-accented assistant is a genuine gap.

---

## 3. Users

| User | Needs |
|---|---|
| **Student** | Ask questions about their subject's material (voice or text) without fear of judgment, get code/answers reviewed and graded with clear corrections, take generated tests, see their own progress per subject over time. |
| **Teacher (real, human)** | Bulk-ingest their subject's syllabus/textbooks once ("library mode"); define/adjust test scope and grading rubrics; review and override any grade or test the virtual teacher issued; see all students' records for their subject. |
| **Virtual Teacher (SmilAI instance)** | Not a human user — a configured instance of the SmilAI brain, assigned by admin to one subject (and grade band), scoped to that subject's knowledge base and rubric. This is what students actually interact with day to day. |
| **Institution admin** | Install and manage the system on their own server; create subjects and grade levels/classes; assign a real teacher to own each subject (who in turn configures their virtual teacher); manage accounts; no dependency on external APIs or internet. |
| **Us (vendor)** | Ship an installable, updateable product; keep the API stable so new front ends and new subjects can be added without touching the brain. |

### Subject and grade scope (v1 target, expanding later)

- **Grade bands:** Nursery through Class 12 (Indian curriculum) is the long-term target.
  **Do not build for all grade bands at once** — pilot one grade band first.
- **V1 subject catalog (concrete, confirmed):** **English, Telugu, Hindi, Mathematics,
  Science, Social Studies** — the standard Indian school subject set. Pilot **one**
  of these six first (recommend Maths or Science — most naturally test-and-grade
  friendly), prove the full loop, then configure the remaining five into the same
  framework (Phase 5 gate, PRD §9) before adding anything beyond this list.
- **Language subjects are two different things — do not conflate them:**
  1. **Telugu/Hindi as a taught subject** — grammar, comprehension, literature. This is
     content and assessment generation *in that language* (question text, answer
     verification), independent of what language the student speaks to SmilAI in.
  2. **Telugu/Hindi as an interaction language** (voice/UI) — a student speaking to
     SmilAI in Telugu instead of English. This is the STT/TTS phase (PRD roadmap P7)
     and can lag behind #1 — a student can study the Telugu *subject* through
     English-medium interaction before Telugu *voice* support exists.
- **Professional/higher-ed subjects** (engineering, medicine, CA, law) remain
  long-term vision (roadmap P9+) — not part of the v1 catalog above, and not to be
  built until the six-subject school catalog is proven.

---

## 4. The SmilAI persona

- **Name:** SmilAI (working name — confirm no trademark conflicts before final launch).
- **Character brief:** warm, encouraging, patient, non-judgmental — the core reason
  this product exists is to be someone a student is *not* afraid to ask "silly"
  questions. This must hold even when delivering a low test score or critical code
  feedback.
- **One brain, many teacher instances.** There is one underlying persona engine and
  character voice, but admin can create multiple **subject-scoped instances** of it —
  a "Math teacher," a "Coding teacher," a "Science teacher" — each with its own
  knowledge base, rubric, and test scope, while sharing the same core personality and
  voice so the experience feels consistent to a student moving between subjects.
- **Voice:** Indian-accented English, female, natural-sounding, persona-consistent
  (same voice every time, not a generic TTS voice). Telugu, Tamil, Hindi voices follow
  in a later phase.
- **Modality:** works equally by typing or talking — mic in, voice out, always with a
  text transcript alongside (accessibility + review).
- **Consistency:** persona tone must carry through teaching answers, voice answers,
  test questions, and grading feedback, regardless of which subject instance is
  responding — a rubric-driven grade should still "sound like" SmilAI.

---

## 5. Core use cases (v1)

1. **Conversational Q&A over subject material.** Student asks their subject's virtual
   teacher a question (typed or spoken); it answers from that subject's ingested
   material, with citations, in text and optionally voice.
2. **Bulk "library" ingestion.** A teacher uploads a textbook or a full syllabus's
   worth of material once, into their subject; it's chunked and embedded and is then
   available to every student in that subject indefinitely.
3. **Test paper generation.** The virtual teacher generates a test/quiz from the
   subject's ingested material — question count, difficulty, and topic coverage
   configurable by the real teacher — so assessment is grounded in what was actually
   taught, not generic questions.
4. **Answer verification / test grading.** Student answers a generated (or
   teacher-authored) test; the virtual teacher evaluates the answers — objective
   (MCQ/numeric) automatically, subjective (short answer/essay/derivation) via
   rubric-guided LLM evaluation — and returns a score plus explanation per question.
5. **Code submission and grading.** For programming subjects specifically: a student
   uploads a code file or project; SmilAI reads it, scores it against a rubric (v1:
   static analysis — logic-by-reading, structure, style, common bug patterns), and
   returns a mark plus specific, actionable corrections.
6. **Subject-based student records.** Every student has a running record **per
   subject** — test scores, code grades, topics they've struggled with — visible to
   the student and their real teacher, not merged across unrelated subjects.
7. **Admin subject/teacher assignment.** Admin creates a subject and grade/class,
   assigns a real teacher to own it; that teacher configures their virtual teacher
   instance (ingest material, set rubric/test defaults).
8. **Voice interaction.** Student can speak a question via mic; SmilAI transcribes,
   answers, and can speak the answer back in her voice — same across every subject.
9. **OCR'd PDFs.** Scanned textbook pages can be ingested (OCR'd to text) and used the
   same as any other document, in any subject.

## 6. Explicitly out of scope for v1

- Building out every subject and grade band at once — v1 proves the loop on **one
  subject, one grade band**; more subjects are a configuration exercise afterward
  (see §3 and roadmap).
- Running/executing student code for functional test-case grading (Phase — needs a
  sandboxing subsystem, described in the SRS).
- Telugu/Tamil/Hindi voice and STT (later phase — English-Indian-accent ships first).
- Multi-institution SaaS / cloud hosting — v1 is on-prem, one server per institution.
- Plagiarism detection across students (worth a future phase, not v1).
- Mobile app front end (API supports it later; not built in v1).

---

## 7. Deployment model

- **On-premise install, LAN-served.** We provide the server software + models; the
  institution provides (or we help spec) the hardware. v1 target hardware: **single
  RTX 3060 12GB** GPU box, installed on the institution's local network. **No internet
  dependency at runtime, ever** — not for models, not for licensing checks, not for
  anything.
- **Many devices, one server.** The server must serve a full computer lab or
  classroom's worth of student/teacher devices **at the same time over LAN** (each
  student on their own PC/tablet browser hitting the same on-prem server by local
  address) — this is not a single-user desktop app.
- **No paid API keys — permanent, not a v1 shortcut.** Every inference call, at every
  phase of the roadmap, runs on local models on this hardware. If a future feature
  seems to need a cloud service, the answer is a local alternative or "not yet," never
  an API key.
- **We provide the front end**, but the API is designed so the institution — or us,
  later — can build other front ends (mobile, kiosk, LMS plugin) against the same
  brain, unchanged.
- **Library mode vs. student mode:** the system must clearly distinguish
  org-wide/subject-wide knowledge (teacher-ingested, persistent, shared) from any
  personal/session content (a student's own code submission), even though both use the
  same underlying ingestion pipeline.

---

## 8. Success metrics (define concretely with a pilot institution before Phase 3 sign-off)

- Retrieval accuracy on a real course's material (target agreed with pilot teacher).
- Grading agreement: sample of SmilAI-graded submissions vs. teacher's own grade,
  within an agreed tolerance.
- Voice round-trip latency (speak → transcribed → answered → spoken back).
- Uptime / stability on the target hardware under expected concurrent student load.

---

## 9. Roadmap (phased — do not build out of order, and do not widen subject/grade
scope before Phase 5)

| Phase | Delivers |
|---|---|
| **P1 — Foundation** | Accounts/roles (student, teacher, admin), org-scoped storage, admin can create ONE subject + grade band, assign ONE real teacher, base API, basic text chat RAG. |
| **P2 — Voice** | faster-whisper STT, two-tier TTS (Indic Parler-TTS main + Piper fallback), mic-in/speaker-out in the UI — built once, works for every future subject. |
| **P3 — Assessment engine** | Test paper generation from ingested material + answer verification (objective auto-graded, subjective rubric-guided), subject-based student records. Piloted on the one subject from P1. |
| **P4 — Code grading (static)** | Upload code/project, rubric-based static grading with corrections — for programming subjects specifically. |
| **P5 — Generalize the subject framework** | Prove that adding a **second** subject (and a second grade band) requires only configuration (ingest material, set rubric/test defaults, assign teacher) — no new code. This is the gate before scaling subject count. |
| **P6 — Library-scale ingestion + OCR** | Bulk textbook ingestion tooling, OCR pipeline for scanned PDFs, chunking tuned for long-form textbook structure — reused by every subject. |
| **P7 — Regional languages** | Telugu, Tamil, Hindi STT + TTS. |
| **P8 — Sandboxed execution grading** | Safe code execution against test cases for functional correctness (separate security-reviewed subsystem). |
| **P9+ (not committed)** | Broaden subject catalog (science, then professional domains — medicine, CA, law, engineering) one at a time using the P5 configuration pattern; plagiarism detection; teacher/admin analytics dashboards; mobile front end; multi-GPU scaling. |

**Why P5 exists as its own phase:** the biggest risk in this plan is trying to build
for nursery-to-12th-plus-four-professional-fields simultaneously — that repeats the
mistake flagged in Project Athena's own early plan ("build for 100 clients before you
have one working"). P5 is the checkpoint that proves the platform generalizes *before*
you commit to scaling subject count.

---

## 10. Open questions to resolve before/while building

- Final product name and voice/persona name clearance (avoid trademark overlap).
- Exact grading rubric structure — is it fixed per subject, or teacher-editable per
  assignment?
- What counts as a "pass" hardware spec if an institution has less than a 3060 —
  do we support a CPU-only degraded mode, or set a hard minimum spec?
- Data retention policy for student submissions and voice recordings.
- Whether teachers can see/override a SmilAI-issued grade before it reaches a student.
