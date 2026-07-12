import { Router } from "express";
import authRouter from "./auth";
import adminRouter from "./admin";
import usersRouter from "./users";
import teacherRouter from "./teacher";
import academicRouter from "./academic";
import contentRouter from "./content";
import chatRouter from "./chat";
import assessmentRouter from "./assessments";
import studentRouter from "./student";

const router = Router();

// Specific routes
router.use("/auth", authRouter);
router.use("/admin", adminRouter);
router.use("/users", usersRouter);
router.use("/teacher", teacherRouter);
router.use("/academic", academicRouter);
router.use("/content", contentRouter);
router.use("/chat", chatRouter);
router.use("/assessments", assessmentRouter);
router.use("/students", studentRouter);

// Flat routes (Aliased for compatibility)
// Note: We use the routers directly here. 
// If a route matches in one, it will be handled. 
// If not, it will fall through to the next.
router.use("/", adminRouter);
router.use("/", academicRouter);
router.use("/", contentRouter);
router.use("/", chatRouter);

export default router;
