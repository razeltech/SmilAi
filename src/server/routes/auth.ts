import { Router } from "express";
import { db } from "../db";

const router = Router();

router.post("/login", async (req, res) => {
  const { email, password } = req.body;
  try {
    const user = await db.get<any>("SELECT * FROM users WHERE email = ? AND password = ?", [email, password]);
    if (!user) {
      return res.status(401).json({ error: "Invalid email or password" });
    }
    res.json({
      id: user.id,
      name: user.name,
      email: user.email,
      role: user.role,
      orgId: user.org_id
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post("/register", async (req, res) => {
  const { name, email, password, role, orgId } = req.body;
  const userId = `user-${Math.random().toString(36).substring(2, 9)}`;
  try {
    await db.run(
      "INSERT INTO users (id, name, email, password, role, org_id) VALUES (?, ?, ?, ?, ?, ?)",
      [userId, name, email, password, role, orgId || "org-prerana"]
    );
    res.status(201).json({ id: userId, name, email, role, orgId });
  } catch (error: any) {
    res.status(400).json({ error: error.message });
  }
});

export default router;
