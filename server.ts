import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import dotenv from "dotenv";

// Import Master Router
import v1Router from "./src/server/routes/index";

dotenv.config();

const app = express();
const PORT = 3000;

app.use(express.json());

// Request Logger
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
  next();
});

// Health Check
app.get("/v1/health", (req, res) => {
  res.json({ status: "ok", database: "sqlite", environment: "AI Studio (Vite+Express)" });
});

// Mount Master Router
app.use("/v1", v1Router);

// API 404 Handler - MUST be after all API routers but BEFORE Vite middleware
app.all("/v1/*", (req, res) => {
  console.log(`API 404: ${req.method} ${req.url}`);
  res.status(404).json({ error: `API route not found: ${req.method} ${req.url}` });
});

// Serving logic
async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
    console.log("Mounted Vite middleware for development");
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`SmilAI Server running on http://localhost:${PORT}`);
  });
}

startServer();
