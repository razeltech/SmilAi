import { Router } from "express";
import { db } from "../db";

const router = Router();

router.post("/profile-approval", async (req, res) => {
  try {
    const { userId, name, phone, bio, qualification, specialization } = req.body;
    const user = await db.get("SELECT * FROM users WHERE id = ?", [userId]);
    if (!user) {
      return res.status(404).json({ error: "User not found" });
    }
    
    const approvalId = `appr-${Math.random().toString(36).substring(2, 9)}`;
    const createdAt = new Date().toISOString();
    
    await db.run("DELETE FROM profile_approvals WHERE userId = ? AND status = 'pending'", [userId]);
    
    await db.run(
      `INSERT INTO profile_approvals (id, userId, teacherName, name, phone, bio, qualification, specialization, status, createdAt)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)`,
      [approvalId, userId, user.name, name, phone, bio, qualification, specialization, createdAt]
    );
    
    res.json({ 
      success: true, 
      approval: { id: approvalId, userId, teacherName: user.name, name, phone, bio, qualification, specialization, status: 'pending', createdAt } 
    });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

router.get("/:userId/pending-approval", async (req, res) => {
  try {
    const { userId } = req.params;
    const pending = await db.get("SELECT * FROM profile_approvals WHERE userId = ? AND status = 'pending'", [userId]);
    res.json(pending || null);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
