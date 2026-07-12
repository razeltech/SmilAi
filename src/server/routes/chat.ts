import { Router } from "express";
import { db } from "../db";
import { performLocalSearch } from "../utils/search";
import { GoogleGenAI } from "@google/genai";
import fetch from "node-fetch";

const router = Router();

router.get("/sessions", async (req, res) => {
  const { userId, subjectId } = req.query;
  try {
    const sessions = await db.all(
      "SELECT * FROM chat_sessions WHERE user_id = ? AND subject_id = ? ORDER BY created_at DESC",
      [userId, subjectId]
    );
    res.json(sessions);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get("/sessions/:id/messages", async (req, res) => {
  try {
    const messages = await db.all(
      "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC",
      [req.params.id]
    );
    const formatted = messages.map((msg: any) => ({
      ...msg,
      citations: msg.citations ? JSON.parse(msg.citations) : []
    }));
    res.json(formatted);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post("/", async (req, res) => {
  const { sessionId, userId, subjectId, message, docId, useOllama, ollamaUrl, ollamaModel } = req.body;
  let currentSessionId = sessionId;

  try {
    if (!currentSessionId) {
      currentSessionId = `session-${Math.random().toString(36).substring(2, 9)}`;
      const title = message.length > 30 ? message.substring(0, 30) + "..." : message;
      await db.run(
        "INSERT INTO chat_sessions (id, user_id, subject_id, title, created_at) VALUES (?, ?, ?, ?, ?)",
        [currentSessionId, userId, subjectId, title, new Date().toISOString()]
      );
    }

    const userMsgId = `msg-${Math.random().toString(36).substring(2, 9)}`;
    await db.run(
      "INSERT INTO chat_messages (id, session_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
      [userMsgId, currentSessionId, "user", message, new Date().toISOString()]
    );

    let chunks: { id: string; text: string }[] = [];
    if (docId && docId !== "all") {
      chunks = await db.all<{ id: string; text: string }>(
        "SELECT c.id, c.text FROM chunks c INNER JOIN documents d ON c.doc_id = d.id WHERE c.subject_id = ? AND c.doc_id = ? AND (d.status != 'needs_review' OR d.status IS NULL)",
        [subjectId, docId]
      );
    } else {
      chunks = await db.all<{ id: string; text: string }>(
        "SELECT c.id, c.text FROM chunks c INNER JOIN documents d ON c.doc_id = d.id WHERE c.subject_id = ? AND (d.status != 'needs_review' OR d.status IS NULL)",
        [subjectId]
      );
    }

    const relevantChunks = performLocalSearch(chunks, message, 3);
    const contextText = relevantChunks.map((c, idx) => `[Citation ${idx + 1}]: ${c.text}`).join("\n\n");

    const subject = await db.get<{ name: string }>("SELECT name FROM subjects WHERE id = ?", [subjectId]);
    const subjectName = subject ? subject.name : "this subject";

    const systemPrompt = `You are "SmilAI", a highly supportive, extremely patient, and warm virtual teacher for ${subjectName}.
Your core mission is to make learning welcoming and comfortable, especially for students who might feel shy or afraid to ask "silly" questions.
Answer with maximum empathy, patience, and direct clarity, using gentle Indian English phrasing (supportive, respectful, encouraging) but keeping it globally accessible.

CRITICAL INSTRUCTIONS:
- You MUST answer the user's question by grounding it strictly in the provided Context material.
- ALWAYS use inline citations such as "[Citation 1]" when referring to facts from the context.
- If the answer cannot be found or deduced from the context, gently explain what you know and suggest related topics covered in the context, maintaining your friendly SmilAI voice. Never invent facts.`;

    const userPrompt = `Context:
${contextText || "No context documents are uploaded yet for this subject. Instruct the user to upload materials first if they are the teacher."}

User Question: "${message}"`;

    let aiResponseText = `Namaste! This is a simulated offline response from SmilAI. Since we are running in an offline prototype mode without GenAI, I am returning this placeholder. You asked: "${message}".`;

    if (useOllama) {
      try {
        const targetUrl = (ollamaUrl || "http://localhost:11434").replace(/\/$/, "");
        const ollamaRes = await fetch(`${targetUrl}/api/generate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            model: ollamaModel || "llama3.2",
            prompt: `${systemPrompt}\n\n${userPrompt}`,
            stream: false
          })
        });
        if (ollamaRes.ok) {
          const ollamaData: any = await ollamaRes.json();
          if (ollamaData && ollamaData.response) {
            aiResponseText = ollamaData.response;
          }
        }
      } catch (e) {}
    } else if (process.env.GEMINI_API_KEY) {
      try {
        const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
        const response = await ai.models.generateContent({
          model: "gemini-1.5-flash",
          contents: userPrompt,
          config: {
            systemInstruction: systemPrompt,
          }
        });
        if (response.text) {
          aiResponseText = response.text;
        }
      } catch (e) {}
    }

    const assistantMsgId = `msg-${Math.random().toString(36).substring(2, 9)}`;
    const citationsList = relevantChunks.map((c, idx) => ({
      tag: `Citation ${idx + 1}`,
      text: c.text,
      id: c.id
    }));

    await db.run(
      "INSERT INTO chat_messages (id, session_id, role, content, timestamp, citations) VALUES (?, ?, ?, ?, ?, ?)",
      [
        assistantMsgId,
        currentSessionId,
        "assistant",
        aiResponseText,
        new Date().toISOString(),
        JSON.stringify(citationsList),
      ]
    );

    res.json({
      sessionId: currentSessionId,
      message: {
        id: assistantMsgId,
        role: "assistant",
        content: aiResponseText,
        timestamp: new Date().toISOString(),
        citations: citationsList,
      },
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
