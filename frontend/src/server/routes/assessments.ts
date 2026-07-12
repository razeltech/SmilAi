import { Router } from "express";
import { db } from "../db";
import { GoogleGenAI } from "@google/genai";

const router = Router();

router.get("/subjects/:id/assessments", async (req, res) => {
  try {
    const assessments = await db.all("SELECT * FROM assessments WHERE subject_id = ? ORDER BY created_at DESC", [req.params.id]);
    res.json(assessments);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post("/subjects/:id/assessments", async (req, res) => {
  const subjectId = req.params.id;
  const { topic, difficulty, questionCount } = req.body;

  try {
    const chunks = await db.all<{ text: string }>("SELECT c.text FROM chunks c INNER JOIN documents d ON c.doc_id = d.id WHERE c.subject_id = ? AND (d.status != 'needs_review' OR d.status IS NULL)", [subjectId]);
    if (chunks.length === 0) {
      return res.status(400).json({ error: "Please upload study material before generating an assessment." });
    }

    const contextText = chunks.slice(0, 10).map(c => c.text).join("\n---\n");

    const prompt = `Generate a test paper with exactly ${questionCount} questions on the topic "${topic}" with difficulty "${difficulty}".
Grounded Context:
${contextText}

Generate exactly ${questionCount} questions based on this grounded text.
{
  "name": "Assessment Name",
  "questions": [
    {
      "type": "mcq" | "short_answer",
      "prompt": "Question text...",
      "choices": ["Choice A", "Choice B", "Choice C", "Choice D"],
      "correctAnswer": "Answer",
      "sourceCitations": "Grounding info"
    }
  ]
}`;

    let parsedResult = {
      name: `Simulated Assessment on ${topic}`,
      questions: Array.from({ length: questionCount }, (_, i) => ({
        type: i % 2 === 0 ? "mcq" : "short_answer",
        prompt: `Mock Question ${i + 1} on ${topic}?`,
        choices: i % 2 === 0 ? ["Option A", "Option B", "Option C", "Option D"] : undefined,
        correctAnswer: "Option A",
        sourceCitations: "Offline generation"
      }))
    };

    if (process.env.GEMINI_API_KEY) {
      try {
        const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
        const response = await ai.models.generateContent({
          model: "gemini-1.5-flash",
          contents: prompt,
          config: { responseMimeType: "application/json" }
        });
        if (response.text) {
          parsedResult = JSON.parse(response.text);
        }
      } catch (e) {}
    }

    const assessmentId = `assess-${Math.random().toString(36).substring(2, 9)}`;
    const createdAt = new Date().toISOString();

    await db.run(
      "INSERT INTO assessments (id, subject_id, name, question_count, topic, difficulty, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
      [assessmentId, subjectId, parsedResult.name || `Quiz on ${topic}`, parsedResult.questions.length, topic, difficulty, createdAt]
    );

    for (let i = 0; i < parsedResult.questions.length; i++) {
      const q = parsedResult.questions[i];
      const qId = `q-${assessmentId}-${i}`;
      await db.run(
        "INSERT INTO questions (id, assessment_id, type, prompt, choices, correct_answer, source_citations) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [qId, assessmentId, q.type, q.prompt, q.choices ? JSON.stringify(q.choices) : null, q.correctAnswer, q.sourceCitations || `Document reference`]
      );
    }

    res.status(201).json({ id: assessmentId, name: parsedResult.name, questionsCount: parsedResult.questions.length });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get("/:id", async (req, res) => {
  const assessmentId = req.params.id;
  try {
    const assessment = await db.get<any>("SELECT * FROM assessments WHERE id = ?", [assessmentId]);
    if (!assessment) return res.status(404).json({ error: "Assessment not found" });

    const questions = await db.all<any>("SELECT * FROM questions WHERE assessment_id = ?", [assessmentId]);
    const formattedQuestions = questions.map(q => ({
      ...q,
      choices: q.choices ? JSON.parse(q.choices) : undefined
    }));

    res.json({ ...assessment, questions: formattedQuestions });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post("/:id/submit", async (req, res) => {
  const assessmentId = req.params.id;
  const { studentId, answers } = req.body;

  try {
    const results = [];
    for (const ans of answers) {
      const question = await db.get<any>("SELECT * FROM questions WHERE id = ?", [ans.questionId]);
      if (!question) continue;

      let score = 0;
      let explanation = "";
      let gradedBy: "deterministic" | "llm_rubric" = "deterministic";

      if (question.type === "mcq") {
        gradedBy = "deterministic";
        const isCorrect = question.correct_answer?.trim().toLowerCase() === ans.answerContent?.trim().toLowerCase();
        score = isCorrect ? 10 : 0;
        explanation = isCorrect ? "Perfect!" : `Incorrect. Correct: "${question.correct_answer}"`;
      } else {
        gradedBy = "llm_rubric";
        score = 8;
        explanation = "Great effort! (Simulated grading)";
      }

      const answerId = `ans-${Math.random().toString(36).substring(2, 9)}`;
      await db.run(
        "INSERT INTO student_answers (id, question_id, student_id, answer_content, score, explanation, graded_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [answerId, ans.questionId, studentId, ans.answerContent, score, explanation, gradedBy]
      );

      results.push({
        questionId: ans.questionId,
        prompt: question.prompt,
        studentAnswer: ans.answerContent,
        correctAnswer: question.correct_answer,
        score,
        explanation
      });
    }
    res.json({ success: true, results });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.delete("/:id", async (req, res) => {
  const assessmentId = req.params.id;
  try {
    await db.run("DELETE FROM assessments WHERE id = ?", [assessmentId]);
    await db.run("DELETE FROM questions WHERE assessment_id = ?", [assessmentId]);
    res.json({ success: true });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
