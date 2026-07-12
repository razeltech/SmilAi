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
    created_at TEXT NOT NULL,
    FOREIGN KEY(subject_id) REFERENCES subjects(id)
);

CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    assessment_id TEXT NOT NULL,
    type TEXT CHECK(type IN ('mcq', 'short_answer')) NOT NULL,
    prompt TEXT NOT NULL,
    choices TEXT,
    correct_answer TEXT,
    source_citations TEXT,
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
