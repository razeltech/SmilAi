import Database from 'better-sqlite3';
const db = new Database('smilai.db');

// Add second teacher
db.prepare("INSERT INTO users (id, name, email, password, role, org_id, phone, bio, designation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)").run(
  'user-teacher2', 'Ms. Reddy', 'reddy@school.org', 'password', 'teacher', 'org-prerana', '+91 91234 56789', 'Experienced Science educator.', 'Science Teacher'
);

// Update Science subject to belong to second teacher
db.prepare("UPDATE subjects SET teacher_id = ? WHERE id = ?").run(
  'user-teacher2', 'subject-science'
);

console.log("Teacher 2 added and assigned to Science!");
