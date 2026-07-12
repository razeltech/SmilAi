import { Router } from "express";
import { db } from "../db";

const router = Router();

router.get("/:id/profile", async (req, res) => {
  try {
    const { id } = req.params;
    const user = await db.get("SELECT * FROM users WHERE id = ?", [id]);
    if (!user) {
      return res.status(404).json({ error: "User not found" });
    }
    res.json({
      id: user.id,
      name: user.name,
      email: user.email,
      role: user.role,
      orgId: user.org_id,
      phone: user.phone || '',
      bio: user.bio || '',
      designation: user.designation || '',
      qualification: user.qualification || '',
      specialization: user.specialization || '',
      class: user.class || '',
      rollNumber: user.rollNumber || '',
      dob: user.dob || '',
      guardianName: user.guardianName || '',
      guardianPhone: user.guardianPhone || '',
      mediumOfInstruction: user.mediumOfInstruction || ''
    });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

router.post("/:id/profile", async (req, res) => {
  try {
    const { id } = req.params;
    const { name, phone, bio, designation } = req.body;
    const user = await db.get("SELECT * FROM users WHERE id = ?", [id]);
    if (!user) {
      return res.status(404).json({ error: "User not found" });
    }
    
    if (user.role === 'admin') {
      await db.run(
        `UPDATE users SET name = ?, phone = ?, bio = ?, designation = ? WHERE id = ?`,
        [name || user.name, phone || user.phone || null, bio || user.bio || null, designation || user.designation || null, id]
      );
      const updatedUser = await db.get("SELECT * FROM users WHERE id = ?", [id]);
      return res.json({ success: true, user: updatedUser });
    } else {
      return res.status(400).json({ error: "Only administrative staff can update their profile directly here. Staff updates require approval." });
    }
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
