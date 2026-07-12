import { Router } from "express";
import { db } from "../db";
import { PythonParser, CppParser, OCRParser } from "../parsers";
import { GoogleGenAI } from "@google/genai";

const router = Router();

// Documents & Library Ingestion
router.get("/subjects/:id/documents", async (req, res) => {
  const subjectId = req.params.id;
  try {
    const docs = await db.all("SELECT * FROM documents WHERE subject_id = ? ORDER BY uploaded_at DESC", [subjectId]);
    res.json(docs);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post("/subjects/:id/documents/bulk", async (req, res) => {
  const subjectId = req.params.id;
  const docsToProcess = req.body.documents || [req.body];
  const orgId = req.body.orgId || docsToProcess[0]?.orgId || "org-prerana";
  const uploadedAt = new Date().toISOString();
  
  let totalChunks = 0;
  let processedDocs = [];

  try {
    for (const doc of docsToProcess) {
      if (!doc.name || !doc.content) continue;
      const docId = `doc-${Math.random().toString(36).substring(2, 9)}`;
      let chunks: string[] = [];
      const filenameLower = doc.name.toLowerCase();
      let status = "active";
      let confidenceScore = "";
          
      let activeParser: "python" | "cpp" | "ocr" | "text" = "text";
      if (doc.parserType === "python" || (doc.parserType === "auto" && filenameLower.endsWith(".py"))) {
        activeParser = "python";
      } else if (doc.parserType === "cpp" || (doc.parserType === "auto" && (filenameLower.endsWith(".cpp") || filenameLower.endsWith(".h") || filenameLower.endsWith(".cc") || filenameLower.endsWith(".hpp")))) {
        activeParser = "cpp";
      } else if (doc.parserType === "ocr" || (doc.parserType === "auto" && (filenameLower.endsWith(".png") || filenameLower.endsWith(".jpg") || filenameLower.endsWith(".jpeg") || filenameLower.endsWith(".pdf")))) {
        activeParser = "ocr";
      }

      if (activeParser === "python") {
        const parsedBlocks = PythonParser.parse(doc.content);
        chunks = parsedBlocks.map(b => {
          if (b.type === "class") {
            return `[PYTHON CLASS: ${b.name}]\nSignature: ${b.signature}\nDocstring: ${b.docstring || "No description provided."}\nSource Code:\n${b.content}`;
          } else if (b.type === "function") {
            return `[PYTHON FUNCTION: ${b.name}]\nSignature: ${b.signature}\nDocstring: ${b.docstring || "No description provided."}\nSource Code:\n${b.content}`;
          }
          return b.content;
        });
      } else if (activeParser === "cpp") {
        const parsedBlocks = CppParser.parse(doc.content);
        chunks = parsedBlocks.map(b => {
          if (b.type === "class") {
            return `[C++ CLASS: ${b.name}]\nSource Code:\n${b.content}`;
          } else if (b.type === "struct") {
            return `[C++ STRUCT: ${b.name}]\nSource Code:\n${b.content}`;
          } else if (b.type === "function") {
            return `[C++ FUNCTION: ${b.name}]\nSignature: ${b.signature || b.name}\nSource Code:\n${b.content}`;
          } else if (b.type === "macro") {
            return `[C++ PREPROCESSOR MACRO: ${b.name}]\nDefinition: ${b.content}`;
          }
          return b.content;
        });
      } else if (activeParser === "ocr") {
        const parsedBlocks = OCRParser.cleanScannedLayout(doc.content);
        const confMatch = doc.content.match(/CONFIDENCE:\s*([\d.]+)%/);
        const conf = confMatch ? parseFloat(confMatch[1]) : 100;
        confidenceScore = conf.toString();
        if (conf < 80) {
          status = "needs_review";
        }
        
        chunks = parsedBlocks.map(b => {
          return `[OCR DETECTED BLOCK: ${b.name}]\n${b.docstring || ""}\nExtracted Text:\n${b.content}`;
        });
      } else {
        const rawChunks = doc.content
          .split(/(?=\bUnit\s+\d+|\bChapter\s+\d+|^\d+\.\s+[A-Z\s]+)/m)
          .map((c: string) => c.trim())
          .filter((c: string) => c.length > 20);

        chunks = rawChunks.length > 0 ? rawChunks : doc.content.split(/\n\n+/).filter((c: string) => c.trim().length > 10);
      }

      if (chunks.length === 0) chunks = [doc.content];
      
      const chunkCount = chunks.length;
      totalChunks += chunkCount;

      await db.run(
        "INSERT INTO documents (id, subject_id, org_id, name, content, type, chunk_count, uploaded_at, status, confidence_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [docId, subjectId, orgId, doc.name, doc.content, doc.type || "library", chunkCount, uploadedAt, status, confidenceScore]
      );

      for (let i = 0; i < chunks.length; i++) {
        const chunkId = `chunk-${docId}-${i}`;
        await db.run(
          "INSERT INTO chunks (id, doc_id, org_id, subject_id, text, chunk_index) VALUES (?, ?, ?, ?, ?, ?)",
          [chunkId, docId, orgId, subjectId, chunks[i], i]
        );
      }
      
      processedDocs.push({ id: docId, name: doc.name, chunkCount, parserUsed: activeParser, status, confidenceScore });
    }

    res.status(201).json({ 
      processedCount: processedDocs.length, 
      totalChunks, 
      documents: processedDocs,
      id: processedDocs[0]?.id,
      name: processedDocs[0]?.name,
      chunkCount: processedDocs[0]?.chunkCount,
      parserUsed: processedDocs[0]?.parserUsed
    });
  } catch (error: any) {
    res.status(400).json({ error: error.message });
  }
});

router.post("/documents/:id/approve", async (req, res) => {
  const docId = req.params.id;
  try {
    await db.run("UPDATE documents SET status = 'active' WHERE id = ?", [docId]);
    res.json({ success: true });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.delete("/documents/:id", async (req, res) => {
  const docId = req.params.id;
  try {
    await db.run("DELETE FROM documents WHERE id = ?", [docId]);
    await db.run("DELETE FROM chunks WHERE doc_id = ?", [docId]);
    res.json({ success: true });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Assignments
router.get("/subjects/:id/assignments", async (req, res) => {
  try {
    const assignments = await db.all("SELECT * FROM assignments WHERE subject_id = ? ORDER BY due_date ASC", [req.params.id]);
    res.json(assignments);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post("/assignments", async (req, res) => {
  const { subjectId, title, description, rubric, dueDate } = req.body;
  const id = `assign-${Math.random().toString(36).substring(2, 9)}`;
  try {
    await db.run(
      "INSERT INTO assignments (id, subject_id, title, description, rubric, due_date) VALUES (?, ?, ?, ?, ?, ?)",
      [id, subjectId, title, description, rubric, dueDate]
    );
    res.status(201).json({ id, title, subjectId });
  } catch (error: any) {
    res.status(400).json({ error: error.message });
  }
});

router.delete("/assignments/:id", async (req, res) => {
  const assignmentId = req.params.id;
  try {
    await db.run("DELETE FROM assignments WHERE id = ?", [assignmentId]);
    await db.run("DELETE FROM submissions WHERE assignment_id = ?", [assignmentId]);
    res.json({ success: true });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post("/assignments/:id/submit", async (req, res) => {
  const assignmentId = req.params.id;
  const { studentId, fileName, codeContent } = req.body;
  const submissionId = `sub-${Math.random().toString(36).substring(2, 9)}`;
  const submittedAt = new Date().toISOString();

  try {
    const assignment = await db.get<any>("SELECT * FROM assignments WHERE id = ?", [assignmentId]);
    if (!assignment) return res.status(404).json({ error: "Assignment not found" });

    const prompt = `You are "SmilAI", evaluating a student's code submission statically. Do NOT execute the code.
Assignment: "${assignment.title}"
Description: "${assignment.description}"
Rubric Criteria:
${assignment.rubric}

Student Code Filename: "${fileName}"
Student Code Content:
\`\`\`
${codeContent}
\`\`\`

Evaluate this submission thoroughly. Point out logic bugs, style improvements, and correct algorithms with ultimate encouragement and constructiveness.
Return a JSON object with this exact format:
{
  "score": <number from 0 to 100 representing the total weighted grade>,
  "feedback": "Detailed, styled markdown feedback in the encouraging, patient SmilAI teacher tone. Break down by rubric criteria, state what is perfect, and list exactly what needs correction with gentle hints."
}`;

    let score = 70;
    let feedback = "Well done. Review your syntax for improvements.";

    if (process.env.GEMINI_API_KEY) {
      try {
        const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
        const response = await ai.models.generateContent({
          model: "gemini-1.5-flash",
          contents: prompt,
          config: {
            responseMimeType: "application/json",
            temperature: 0.2
          }
        });
        
        if (response.text) {
          try {
            const result = JSON.parse(response.text);
            score = result.score ?? 70;
            feedback = result.feedback || "Well done. Review your syntax for improvements.";
          } catch (e) {
            console.error("Failed to parse Gemini feedback JSON:", e, response.text);
            feedback = response.text;
          }
        }
      } catch (e) {
        console.error("Failed to call Gemini for code grading:", e);
      }
    } else {
      score = 85;
      feedback = "### SmilAI Feedback\n\nGreat job on your submission! This is a simulated offline response from the static analyzer (No API Key provided).";
    }

    await db.run(
      `INSERT INTO submissions (id, assignment_id, student_id, file_name, code_content, score, feedback, submitted_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [submissionId, assignmentId, studentId, fileName, codeContent, score, feedback, submittedAt]
    );

    res.status(201).json({ submissionId, score, feedback });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get("/subjects/:id/submissions", async (req, res) => {
  const subjectId = req.params.id;
  try {
    const submissions = await db.all<any>(
      `SELECT s.*, u.name as studentName, asg.title as assignmentTitle 
       FROM submissions s 
       JOIN assignments asg ON s.assignment_id = asg.id 
       JOIN users u ON s.student_id = u.id 
       WHERE asg.subject_id = ?`,
      [subjectId]
    );
    res.json(submissions);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post("/submissions/:id/override", async (req, res) => {
  const submissionId = req.params.id;
  const { score, feedback } = req.body;
  try {
    const submission = await db.get("SELECT * FROM submissions WHERE id = ?", [submissionId]);
    if (!submission) {
      return res.status(404).json({ error: "Submission not found" });
    }
    
    const finalScore = score !== undefined ? parseInt(score) : submission.score;
    const finalFeedback = feedback !== undefined ? feedback : submission.feedback;
    
    await db.run(
      `UPDATE submissions SET score = ?, feedback = ? WHERE id = ?`,
      [finalScore, finalFeedback, submissionId]
    );
    
    const updated = await db.get("SELECT * FROM submissions WHERE id = ?", [submissionId]);
    res.json({ success: true, submission: updated });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
