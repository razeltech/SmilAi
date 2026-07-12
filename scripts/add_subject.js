import Database from 'better-sqlite3';
const db = new Database('smilai.db');

const subjectId = 'subject-science';
db.prepare("INSERT INTO subjects (id, org_id, grade_band_id, name, teacher_id) VALUES (?, ?, ?, ?, ?)").run(
  subjectId, 'org-prerana', 'grade-10', 'Science', 'user-teacher'
);

// Enroll the student in Science
db.prepare("INSERT INTO enrollments (user_id, subject_id) VALUES (?, ?)").run(
  'user-student', subjectId
);

// Add an assignment for Science
db.prepare("INSERT INTO assignments (id, subject_id, title, description, rubric, due_date) VALUES (?, ?, ?, ?, ?, ?)").run(
  'assign-sci1', subjectId, 'Gravity Simulation Lab', 'Write a short simulation of a falling object, calculating its velocity over 10 seconds given g=9.8 m/s^2.', 
  '1. Uses variables for time and gravity (20 pts)\n2. Correctly calculates velocity using v=u+at (50 pts)\n3. Outputs results neatly (30 pts)', '2026-08-01'
);

// Add a document (ingested material) for Science
db.prepare("INSERT INTO documents (id, subject_id, org_id, name, content, type, chunk_count, uploaded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)").run(
  'doc-sci1', subjectId, 'org-prerana', 'Chapter 1: Motion and Gravity', 
  'Gravity is a fundamental interaction which causes mutual attraction between all things that have mass. The acceleration due to gravity near Earth surface is approximately 9.8 m/s^2. Velocity is the rate of change of its position with respect to a frame of reference, and is a function of time: v = u + at, where u is initial velocity, a is acceleration, and t is time.',
  'text/plain', '1', new Date().toISOString()
);

// Add chunk for the document
db.prepare("INSERT INTO chunks (id, doc_id, org_id, subject_id, text, chunk_index) VALUES (?, ?, ?, ?, ?, ?)").run(
  'chunk-sci1-1', 'doc-sci1', 'org-prerana', subjectId, 
  'Gravity is a fundamental interaction which causes mutual attraction between all things that have mass. The acceleration due to gravity near Earth surface is approximately 9.8 m/s^2. Velocity is the rate of change of its position with respect to a frame of reference, and is a function of time: v = u + at, where u is initial velocity, a is acceleration, and t is time.', 0
);

console.log("Science subject configured successfully!");
