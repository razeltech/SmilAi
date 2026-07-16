-- SmilAI SQLite Unified Schema
-- This is the single source of truth for the database. Both Node and Python backends must use this to initialize tables.

CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT CHECK(role IN ('student', 'teacher', 'admin')) NOT NULL,
    org_id TEXT NOT NULL,
    FOREIGN KEY(org_id) REFERENCES organizations(id)
);

CREATE TABLE IF NOT EXISTS grade_bands (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY(org_id) REFERENCES organizations(id)
);

CREATE TABLE IF NOT EXISTS subjects (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    grade_band_id TEXT NOT NULL,
    name TEXT NOT NULL,
    teacher_id TEXT NOT NULL,
    category TEXT CHECK(category IN ('GENERAL', 'PROGRAMMING', 'SCIENCE', 'LANGUAGE', 'MEDICAL')) NOT NULL DEFAULT 'GENERAL',
    supports_projects INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT,
    deleted_at TEXT,
    FOREIGN KEY(org_id) REFERENCES organizations(id),
    FOREIGN KEY(grade_band_id) REFERENCES grade_bands(id),
    FOREIGN KEY(teacher_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS enrollments (
    user_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    PRIMARY KEY(user_id, subject_id),
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id)
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    type TEXT CHECK(type IN ('library', 'personal')) NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    uploaded_at TEXT NOT NULL,
    processed_at TEXT,
    status TEXT CHECK(status IN ('pending', 'approved', 'archived')) NOT NULL DEFAULT 'approved',
    FOREIGN KEY(subject_id) REFERENCES subjects(id),
    FOREIGN KEY(org_id) REFERENCES organizations(id)
);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    FOREIGN KEY(doc_id) REFERENCES documents(id),
    FOREIGN KEY(org_id) REFERENCES organizations(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id)
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id)
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT CHECK(role IN ('user', 'assistant')) NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    citations TEXT,
    audio_url TEXT,
    FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
);

CREATE TABLE IF NOT EXISTS assessments (
    id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    name TEXT NOT NULL,
    question_count INTEGER NOT NULL,
    topic TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    status TEXT CHECK(status IN ('draft', 'published', 'archived')) NOT NULL DEFAULT 'published',
    published_at TEXT,
    updated_at TEXT,
    created_at TEXT NOT NULL,
    deleted_at TEXT,
    FOREIGN KEY(subject_id) REFERENCES subjects(id)
);

CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    assessment_id TEXT NOT NULL,
    type TEXT CHECK(type IN ('mcq', 'short_answer')) NOT NULL,
    prompt TEXT NOT NULL,
    choices TEXT,
    correct_answer TEXT,
    explanation TEXT,
    difficulty TEXT CHECK(difficulty IN ('Easy', 'Medium', 'Hard')) NOT NULL DEFAULT 'Medium',
    source_citations TEXT,
    updated_at TEXT,
    FOREIGN KEY(assessment_id) REFERENCES assessments(id)
);

CREATE TABLE IF NOT EXISTS student_answers (
    id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    answer_content TEXT NOT NULL,
    score REAL,
    explanation TEXT,
    graded_by TEXT CHECK(graded_by IN ('deterministic', 'llm_rubric')),
    teacher_override REAL,
    FOREIGN KEY(question_id) REFERENCES questions(id),
    FOREIGN KEY(student_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS assignments (
    id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    rubric TEXT NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT CHECK(status IN ('draft', 'published', 'archived')) NOT NULL DEFAULT 'published',
    created_at TEXT NOT NULL,
    updated_at TEXT,
    published_at TEXT,
    deleted_at TEXT,
    FOREIGN KEY(subject_id) REFERENCES subjects(id)
);

CREATE TABLE IF NOT EXISTS submissions (
    id TEXT PRIMARY KEY,
    assignment_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    code_content TEXT NOT NULL,
    score REAL,
    feedback TEXT,
    teacher_override REAL,
    submitted_at TEXT NOT NULL,
    FOREIGN KEY(assignment_id) REFERENCES assignments(id),
    FOREIGN KEY(student_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS student_memory (
    student_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    memory_type TEXT CHECK(memory_type IN ('ACADEMIC', 'BEHAVIOUR', 'PREFERENCE', 'PROFILE', 'GOAL')) NOT NULL,
    concept TEXT NOT NULL,
    details TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    observation_count INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL,
    PRIMARY KEY(student_id, subject_id, memory_type, concept),
    FOREIGN KEY(student_id) REFERENCES users(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    resource_id TEXT,
    timestamp TEXT NOT NULL,
    metadata TEXT,
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS concept_mastery (
    student_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    concept TEXT NOT NULL,
    mastery_score REAL NOT NULL DEFAULT 0.0,
    confidence REAL NOT NULL DEFAULT 0.0,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    correct_answers INTEGER NOT NULL DEFAULT 0,
    incorrect_answers INTEGER NOT NULL DEFAULT 0,
    last_seen_at TEXT,
    last_mastered_at TEXT,
    review_count INTEGER NOT NULL DEFAULT 0,
    next_review_at TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY(student_id, subject_id, concept),
    FOREIGN KEY(student_id) REFERENCES users(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id)
);

CREATE TABLE IF NOT EXISTS revision_plans (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    concept TEXT NOT NULL,
    priority_score INTEGER NOT NULL DEFAULT 50,
    scheduled_date TEXT NOT NULL,
    status TEXT CHECK(status IN ('pending', 'completed', 'skipped')) NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY(student_id) REFERENCES users(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id)
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_documents_subject ON documents(subject_id);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_student ON student_memory(student_id, subject_id);
CREATE INDEX IF NOT EXISTS idx_assessment_subject ON assessments(subject_id);
