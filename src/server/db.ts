import Database from 'better-sqlite3';
import path from 'path';

const dbPath = path.join(process.cwd(), 'smilai.db');
const sqliteDb = new Database(dbPath);

// Initialize all required tables on startup
sqliteDb.exec(`
CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    boardType TEXT,
    schoolCode TEXT,
    contactEmail TEXT,
    phone TEXT,
    address TEXT,
    mediumOfInstruction TEXT
);

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT CHECK(role IN ('student', 'teacher', 'admin')) NOT NULL,
    org_id TEXT NOT NULL,
    phone TEXT,
    bio TEXT,
    designation TEXT,
    qualification TEXT,
    specialization TEXT,
    class TEXT,
    rollNumber TEXT,
    dob TEXT,
    guardianName TEXT,
    guardianPhone TEXT,
    mediumOfInstruction TEXT,
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
    type TEXT NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    uploaded_at TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    confidence_score REAL,
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

CREATE TABLE IF NOT EXISTS profile_approvals (
    id TEXT PRIMARY KEY,
    userId TEXT NOT NULL,
    teacherName TEXT NOT NULL,
    name TEXT,
    phone TEXT,
    bio TEXT,
    qualification TEXT,
    specialization TEXT,
    status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) NOT NULL,
    createdAt TEXT NOT NULL,
    decidedAt TEXT,
    adminNotes TEXT,
    FOREIGN KEY(userId) REFERENCES users(id)
);
`);

// Auto-seed database if users table is empty
try {
  const userCountRow = sqliteDb.prepare("SELECT COUNT(*) as count FROM users").get() as { count: number };
  if (userCountRow.count === 0) {
    console.log("Empty SQLite database detected. Seeding initial academic data...");
    
    // Seed Organizations
    sqliteDb.prepare(`
      INSERT INTO organizations (id, name, boardType, schoolCode, contactEmail, phone, address, mediumOfInstruction)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      'org-prerana', 
      'Prerana Private Corporate Academy', 
      'private_cbse', 
      'AP-GOVT-522001', 
      'admin@school.org', 
      '+91 866 254124', 
      'Beside Govt Hospital, Vijayawada, Andhra Pradesh, 520001', 
      'English & Telugu'
    );

    // Seed Users
    const insertUser = sqliteDb.prepare(`
      INSERT INTO users (id, name, email, password, role, org_id, phone, bio, designation, qualification, specialization, class, rollNumber, dob, guardianName, guardianPhone, mediumOfInstruction)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    insertUser.run(
      'user-admin', 'Admin Staff', 'admin@school.org', 'password', 'admin', 'org-prerana', 
      '+91 98480 22338', 'Administrative Principal of AP Academic Center. Managing high-performance curriculum structures since 2012.', 
      'Principal / Chief Administrator', null, null, null, null, null, null, null, null
    );

    insertUser.run(
      'user-teacher', 'Mr. Sharma', 'sharma@school.org', 'password', 'teacher', 'org-prerana', 
      '+91 94405 11223', 'Experienced educator specializing in Mathematics and Physical Sciences. Enthusiastic about introducing computational thinking to high school students.', 
      'Senior Educator', 'M.Sc. Mathematics, B.Ed.', 'Algebra, Quadratic Equations, Kinematics', null, null, null, null, null, null
    );

    insertUser.run(
      'user-student', 'Rahul Kumar', 'rahul@school.org', 'password', 'student', 'org-prerana', 
      '+91 70132 45678', null, null, null, null, '10th Class (SSC)', '26SSC10042', '2011-08-15', 'Srinivas Kumar', '+91 98481 98481', 'Telugu & English'
    );

    // Seed Grade Bands
    const insertGradeBand = sqliteDb.prepare("INSERT INTO grade_bands (id, org_id, name) VALUES (?, ?, ?)");
    const gradeBands = [
      ['grade-10', '10th Class (SSC)'],
      ['gb-nursery', 'Nursery'],
      ['gb-lkg', 'Lower KG (LKG)'],
      ['gb-ukg', 'Upper KG (UKG)'],
      ['gb-class-1', '1st Class'],
      ['gb-class-2', '2nd Class'],
      ['gb-class-3', '3rd Class'],
      ['gb-class-4', '4th Class'],
      ['gb-class-5', '5th Class'],
      ['gb-class-6', '6th Class'],
      ['gb-class-7', '7th Class'],
      ['gb-class-8', '8th Class'],
      ['gb-class-9', '9th Class'],
      ['gb-class-11', 'Junior Intermediate (11th Class)'],
      ['gb-class-12', 'Senior Intermediate (12th Class)']
    ];
    for (const gb of gradeBands) {
      insertGradeBand.run(gb[0], 'org-prerana', gb[1]);
    }

    // Seed Subjects
    sqliteDb.prepare("INSERT INTO subjects (id, org_id, grade_band_id, name, teacher_id) VALUES (?, ?, ?, ?, ?)").run(
      'subject-math', 'org-prerana', 'grade-10', 'Mathematics', 'user-teacher'
    );
    sqliteDb.prepare("INSERT INTO subjects (id, org_id, grade_band_id, name, teacher_id) VALUES (?, ?, ?, ?, ?)").run(
      'subject-gsfrljm', 'org-prerana', 'gb-nursery', '[AP-SSC-104] Mathematics (గణితము)', 'user-teacher'
    );

    // Seed Enrollments
    sqliteDb.prepare("INSERT INTO enrollments (user_id, subject_id) VALUES (?, ?)").run(
      'user-student', 'subject-math'
    );

    // Seed Documents
    sqliteDb.prepare(`
      INSERT INTO documents (id, subject_id, org_id, name, content, type, chunk_count, uploaded_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      'doc-quadratic', 'subject-math', 'org-prerana', 'Unit 1: Quadratic Equations',
      `CHAPTER: Quadratic Equations

1. INTRODUCTION TO QUADRATIC EQUATIONS
A quadratic equation is a polynomial equation of the second degree. The general form of a quadratic equation is:
ax^2 + bx + c = 0
where x represents an unknown variable, and a, b, and c represent known numbers, with a not equal to 0. If a = 0, then the equation is linear, not quadratic.
The numbers a, b, and c are the coefficients of the equation and may be distinguished by calling them, respectively, the quadratic coefficient, the linear coefficient and the constant or free term.

2. METHODS OF SOLVING QUADRATIC EQUATIONS
There are three main methods used to solve quadratic equations:
A. Factoring (Factoring by grouping or splitting the middle term).
B. Completing the Square.
C. The Quadratic Formula.

The Quadratic Formula is expressed as:
x = (-b ± √(b^2 - 4ac)) / (2a)
The term inside the square root, (b^2 - 4ac), is called the Discriminant (D).

3. THE DISCRIMINANT AND THE NATURE OF ROOTS
The Discriminant D = b^2 - 4ac determines the nature of the roots of the quadratic equation:
- If D > 0, there are two distinct real roots.
- If D = 0, there is exactly one real root (also called a repeated or double root).
- If D < 0, there are two complex (imaginary) roots.

4. REAL WORLD APPLICATIONS
Quadratic equations are used to model the trajectory of projectiles (like throwing a ball or firing a rocket), optimization in business (profit maximization), and calculating areas of shapes.`,
      'text/plain', 4, '2026-07-11T06:56:16.887Z'
    );

    // Seed Chunks
    const insertChunk = sqliteDb.prepare(`
      INSERT INTO chunks (id, doc_id, org_id, subject_id, text, chunk_index)
      VALUES (?, ?, ?, ?, ?, ?)
    `);

    insertChunk.run(
      'chunk-quad-0', 'doc-quadratic', 'org-prerana', 'subject-math',
      'INTRODUCTION TO QUADRATIC EQUATIONS\nA quadratic equation is a polynomial equation of the second degree. The general form of a quadratic equation is: ax^2 + bx + c = 0, where x is an unknown, and a, b, and c are coefficients with a != 0. If a = 0, the equation is linear.',
      0
    );
    insertChunk.run(
      'chunk-quad-1', 'doc-quadratic', 'org-prerana', 'subject-math',
      'METHODS OF SOLVING QUADRATIC EQUATIONS\nThere are three main methods to solve quadratic equations:\nA. Factoring (splitting the middle term).\nB. Completing the square.\nC. The Quadratic Formula.\nThe quadratic formula is x = (-b ± √(b^2 - 4ac)) / (2a).',
      1
    );
    insertChunk.run(
      'chunk-quad-2', 'doc-quadratic', 'org-prerana', 'subject-math',
      'THE DISCRIMINANT AND THE NATURE OF ROOTS\nThe term inside the square root, D = b^2 - 4ac, is called the Discriminant.\n- If D > 0, there are two distinct real roots.\n- If D = 0, there is exactly one repeated real root.\n- If D < 0, there are two complex (imaginary) roots.',
      2
    );
    insertChunk.run(
      'chunk-quad-3', 'doc-quadratic', 'org-prerana', 'subject-math',
      'REAL WORLD APPLICATIONS\nQuadratic equations are used extensively to model projectile motion (the path of a ball or rocket), optimize profit margins in financial calculations, and solve geometric area problems where dimensions depend on one another.',
      3
    );

    // Seed Assignments
    sqliteDb.prepare(`
      INSERT INTO assignments (id, subject_id, title, description, rubric, due_date)
      VALUES (?, ?, ?, ?, ?, ?)
    `).run(
      'assign-intro-coding', 'subject-math', 'Assignment 1: Solving Quadratic Equations in Code',
      'Write a Python program that asks the user for coefficients a, b, and c of a quadratic equation ax^2 + bx + c = 0, calculates the discriminant, and prints the roots. Handle all cases: D > 0, D = 0, and D < 0.',
      'Correctness (40%): Correctly calculates discriminant and roots in all cases.\nCode Style (30%): Clean variable naming, proper comments, and clear user inputs.\nInput Validation (30%): Handles case where a = 0 gracefully (notifying that it is a linear equation).',
      '2026-07-18'
    );

    // Seed Submissions
    sqliteDb.prepare(`
      INSERT INTO submissions (id, assignment_id, student_id, file_name, code_content, score, feedback, submitted_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      'sub-aygjbnk', 'assign-intro-coding', 'user-student', 'solution.py', 'print("Hello, Quadratic Solver")',
      85, '### SmilAI Feedback\n\nGreat job on your submission! This is a simulated offline response from the static analyzer.',
      '2026-07-11T07:14:29.938Z'
    );

    console.log("Database seeded successfully!");
  }
} catch (e) {
  console.error("Database schema checking or seeding failed:", e);
}

export const db = {
  run: async (sql: string, params: any[] = []) => {
    return new Promise((resolve, reject) => {
      try {
        const info = sqliteDb.prepare(sql).run(...params);
        resolve({ lastID: info.lastInsertRowid, changes: info.changes });
      } catch (err) {
        reject(err);
      }
    });
  },
  get: async <T = any>(sql: string, params: any[] = []): Promise<T | undefined> => {
    return new Promise((resolve, reject) => {
      try {
        const row = sqliteDb.prepare(sql).get(...params);
        resolve(row as T | undefined);
      } catch (err) {
        reject(err);
      }
    });
  },
  all: async <T = any>(sql: string, params: any[] = []): Promise<T[]> => {
    return new Promise((resolve, reject) => {
      try {
        const rows = sqliteDb.prepare(sql).all(...params);
        resolve(rows as T[]);
      } catch (err) {
        reject(err);
      }
    });
  }
};

