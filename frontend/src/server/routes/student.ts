import { Router } from "express";
import { db } from "../db";

const router = Router();

router.get("/:id/subjects/:subject_id/record", async (req, res) => {
  const studentId = req.params.id;
  const subjectId = req.params.subject_id;

  try {
    const student = await db.get<any>("SELECT id, name FROM users WHERE id = ?", [studentId]);
    const subject = await db.get<any>("SELECT id, name FROM subjects WHERE id = ?", [subjectId]);

    if (!student || !subject) {
      return res.status(404).json({ error: "Student or Subject not found" });
    }

    const assessments = await db.all<any>(`
      SELECT a.name as assessmentName, AVG(sa.score) as avgScore, SUM(sa.score) as totalScore, COUNT(sa.id) as questionCount, a.created_at as date
      FROM assessments a
      JOIN questions q ON q.assessment_id = a.id
      JOIN student_answers sa ON sa.question_id = q.id
      WHERE a.subject_id = ? AND sa.student_id = ?
      GROUP BY a.id
    `, [subjectId, studentId]);

    const submissions = await db.all<any>(`
      SELECT asg.title, s.score, s.submitted_at as date
      FROM submissions s
      JOIN assignments asg ON s.assignment_id = asg.id
      WHERE asg.subject_id = ? AND s.student_id = ?
    `, [subjectId, studentId]);

    const assessmentsCompleted = assessments.length;
    let avgScore = 0;
    if (assessmentsCompleted > 0) {
      const sum = assessments.reduce((acc, curr) => acc + (curr.avgScore * 10), 0);
      avgScore = Math.round(sum / assessmentsCompleted);
    }

    res.json({
      studentId: student.id,
      studentName: student.name,
      subjectId: subject.id,
      subjectName: subject.name,
      assessmentsCompleted,
      averageScore: avgScore,
      submissionsCompleted: submissions.length,
      recentAssessments: assessments.map(a => ({
        assessmentName: a.assessmentName,
        score: Math.round(a.avgScore * 10),
        total: 100,
        date: a.date.split("T")[0]
      })),
      recentSubmissions: submissions.map(s => ({
        title: s.title,
        score: s.score,
        date: s.date.split("T")[0]
      }))
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
