import { Router } from "express";
import { db } from "../db";

const router = Router();

// Grade Bands
router.get("/grade-bands", async (req, res) => {
  try {
    const bands = await db.all("SELECT * FROM grade_bands");
    res.json(bands);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post("/grade-bands", async (req, res) => {
  const { name, orgId } = req.body;
  const id = `grade-${Math.random().toString(36).substring(2, 9)}`;
  try {
    await db.run("INSERT INTO grade_bands (id, org_id, name) VALUES (?, ?, ?)", [id, orgId || "org-prerana", name]);
    res.status(201).json({ id, name, orgId });
  } catch (error: any) {
    res.status(400).json({ error: error.message });
  }
});

// Subjects
router.get("/subjects", async (req, res) => {
  const { userId, role } = req.query;
  try {
    let sql = `
      SELECT DISTINCT s.*, u.name as teacherName, g.name as gradeBandName 
      FROM subjects s
      LEFT JOIN users u ON s.teacher_id = u.id
      LEFT JOIN grade_bands g ON s.grade_band_id = g.id
    `;
    let params: any[] = [];
    
    if (role === 'teacher') {
      sql += ` WHERE s.teacher_id = ?`;
      params.push(userId);
    } else if (role === 'student') {
      sql += ` INNER JOIN enrollments e ON s.id = e.subject_id WHERE e.user_id = ?`;
      params.push(userId);
    }

    const subjects = await db.all(sql, params);
    res.json(subjects);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post("/subjects", async (req, res) => {
  const { name, gradeBandId, teacherId, orgId } = req.body;
  const id = `subject-${Math.random().toString(36).substring(2, 9)}`;
  try {
    await db.run(
      "INSERT INTO subjects (id, org_id, grade_band_id, name, teacher_id) VALUES (?, ?, ?, ?, ?)",
      [id, orgId || "org-prerana", gradeBandId, name, teacherId]
    );
    res.status(201).json({ id, name, gradeBandId, teacherId });
  } catch (error: any) {
    res.status(400).json({ error: error.message });
  }
});

router.delete("/subjects/:id", async (req, res) => {
  const { id } = req.params;
  try {
    await db.run("DELETE FROM subjects WHERE id = ?", [id]);
    await db.run("DELETE FROM enrollments WHERE subject_id = ?", [id]);
    await db.run("DELETE FROM documents WHERE subject_id = ?", [id]);
    await db.run("DELETE FROM chunks WHERE subject_id = ?", [id]);
    res.json({ success: true });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post("/subjects/:id/enroll", async (req, res) => {
  const { userId } = req.body;
  const subjectId = req.params.id;
  try {
    await db.run("INSERT INTO enrollments (user_id, subject_id) VALUES (?, ?)", [userId, subjectId]);
    res.status(201).json({ success: true });
  } catch (error: any) {
    res.status(400).json({ error: error.message });
  }
});

router.get("/subjects/:id/enrollments", async (req, res) => {
  const subjectId = req.params.id;
  try {
    const students = await db.all(`
      SELECT u.id, u.name, u.email 
      FROM enrollments e
      JOIN users u ON e.user_id = u.id
      WHERE e.subject_id = ?
    `, [subjectId]);
    res.json(students);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
