import { Router } from "express";
import { db } from "../db";

const router = Router();

router.get("/users", async (req, res) => {
  const { role } = req.query;
  try {
    let users;
    if (role) {
      users = await db.all("SELECT id, name, email, role, org_id as orgId FROM users WHERE role = ?", [role]);
    } else {
      users = await db.all("SELECT id, name, email, role, org_id as orgId FROM users");
    }
    res.json(users);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.delete("/users/:id", async (req, res) => {
  const { id } = req.params;
  try {
    await db.run("DELETE FROM users WHERE id = ?", [id]);
    await db.run("DELETE FROM enrollments WHERE user_id = ?", [id]);
    res.json({ success: true });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get("/org-settings", async (req, res) => {
  try {
    const org = await db.get("SELECT * FROM organizations LIMIT 1") || { id: 'org-prerana', name: 'Andhra Pradesh Government High School', boardType: 'ap_govt_ssc' };
    res.json(org);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

router.post("/org-settings", async (req, res) => {
  try {
    const { name, boardType, schoolCode, contactEmail, phone, address, mediumOfInstruction } = req.body;
    let org = await db.get("SELECT * FROM organizations LIMIT 1");
    if (!org) {
      const orgId = 'org-prerana';
      await db.run(
        `INSERT INTO organizations (id, name, boardType, schoolCode, contactEmail, phone, address, mediumOfInstruction) 
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
        [orgId, name || '', boardType || '', schoolCode || '', contactEmail || '', phone || '', address || '', mediumOfInstruction || '']
      );
      org = { id: orgId, name, boardType, schoolCode, contactEmail, phone, address, mediumOfInstruction };
    } else {
      await db.run(
        `UPDATE organizations 
         SET name = ?, boardType = ?, schoolCode = ?, contactEmail = ?, phone = ?, address = ?, mediumOfInstruction = ? 
         WHERE id = ?`,
        [
          name !== undefined ? name : org.name,
          boardType !== undefined ? boardType : org.boardType,
          schoolCode !== undefined ? schoolCode : org.schoolCode,
          contactEmail !== undefined ? contactEmail : org.contactEmail,
          phone !== undefined ? phone : org.phone,
          address !== undefined ? address : org.address,
          mediumOfInstruction !== undefined ? mediumOfInstruction : org.mediumOfInstruction,
          org.id
        ]
      );
      org = await db.get("SELECT * FROM organizations WHERE id = ?", [org.id]);
    }
    res.json(org);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

router.get("/profile-approvals", async (req, res) => {
  try {
    const approvals = await db.all("SELECT * FROM profile_approvals");
    res.json(approvals);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

router.post("/profile-approvals/:id/decide", async (req, res) => {
  try {
    const { id } = req.params;
    const { decision, adminNotes } = req.body;
    const approval = await db.get("SELECT * FROM profile_approvals WHERE id = ?", [id]);
    if (!approval) {
      return res.status(404).json({ error: "Approval request not found" });
    }
    
    const decidedAt = new Date().toISOString();
    const notes = adminNotes || '';
    
    await db.run(
      `UPDATE profile_approvals SET status = ?, decidedAt = ?, adminNotes = ? WHERE id = ?`,
      [decision, decidedAt, notes, id]
    );
    
    if (decision === 'approved') {
      const user = await db.get("SELECT * FROM users WHERE id = ?", [approval.userId]);
      if (user) {
        await db.run(
          `UPDATE users 
           SET name = ?, phone = ?, bio = ?, qualification = ?, specialization = ? 
           WHERE id = ?`,
          [
            approval.name || user.name,
            approval.phone || user.phone,
            approval.bio || user.bio,
            approval.qualification || user.qualification,
            approval.specialization || user.specialization,
            approval.userId
          ]
        );
      }
    }
    
    const updatedApproval = await db.get("SELECT * FROM profile_approvals WHERE id = ?", [id]);
    res.json({ success: true, approval: updatedApproval });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
