# SmilAI — Offline Virtual-Teacher & Assessment Platform

> **🤖 AI SYSTEM NOTICE (READ FIRST)**
> If you are an AI assistant opening this project for the first time, you MUST read the following files before taking any action or writing any code:
> 1. `docs/SmilAI_rules.md` (Persona, Branding, and strict Architectural rules)
> 2. `docs/implementation_plan.md` (Timeline, Phases, and current status)
> 3. `docs/EXPECTED_OUTCOMES.md` (User flows and expectations)
> Failure to read these files will result in violating project constraints.

SmilAI is a fully offline virtual-teacher platform designed for local network deployment. It empowers institutions to set up personalized, infinite-patience virtual mentors (teachers) scoped to specific subject syllabi, textbooks, and grading rubrics.

This repository is split cleanly into a `frontend/` (React + Vite) and `backend/` (Python + FastAPI).

---

## 💾 Saving C-Drive Space: Storing Ollama Models Inside Project Folder

If you are running Ollama locally but have low storage space on your C: drive, you can force Ollama to store its downloaded LLM weights directly inside the project directory (or an external drive). 

To do this, we configure Ollama's model storage path to a local folder named `.models` (which is added to `.gitignore` to prevent committing gigabytes of weights).

### Configuration Steps

#### On Windows (PowerShell / Command Prompt)
Before starting Ollama, set the `OLLAMA_MODELS` environment variable pointing to your project subdirectory:
```powershell
# PowerShell
$env:OLLAMA_MODELS = "C:\path\to\your\smilai\project\.models"
ollama serve

# Command Prompt
set OLLAMA_MODELS=C:\path\to\your\smilai\project\.models
ollama serve
```

#### On macOS & Linux (Terminal)
```bash
export OLLAMA_MODELS="/path/to/your/smilai/project/.models"
ollama serve
```

When you run `ollama pull llama3` or `ollama pull gemma2`, the model weights will download straight into your project's `.models/` folder instead of filling up your system disk.

---

## 🔍 Google-Grade RAG: Offline Hybrid Search (BM25 + Vector)

To maximize accuracy under fully offline constraints without paid APIs, SmilAI uses **Hybrid Search**. This technique matches Google's retrieval strategies by combining:

1. **Keyword-Based BM25 / TF-IDF Retrieval**: Excels at finding exact terms, names, code functions, and mathematical formulas (critical for maths, coding, and science).
2. **Dense Semantic Embedding Distance**: Captures conceptual meaning, synonyms, and phrasing variations.
3. **Reciprocal Rank Fusion (RRF)**: Re-ranks and merges the results of both search strategies into a single high-quality context stream for the local LLM.

SQLite's Full-Text Search (`FTS5`) serves as the ultra-light keyword engine, while the local embedding database acts as the semantic engine.

---

## 🛠️ Code Parsers & OCR Ingestion Pipelines

To keep shared modules clean, SmilAI implements a centralized **Parser Registry Pattern**. All documents pass through specialized extractors:

*   **Python Code Parser (`PythonParser`)**: Extracts AST structures, classes, functions, and docstrings so the teacher understands code semantics rather than treating it as raw text.
*   **C / C++ Code Parser (`CppParser`)**: Isolates preprocessor directives, structs, function headers, and class definitions to provide precise context in the knowledge base.
*   **OCR PDF/Image Ingestion (`OCRParser`)**: Employs Tesseract/local extraction to parse scanned textbook pages, diagrams, or printed exam sheets, flagging low-confidence blocks for human teacher auditing.

---

## 🚀 Porting to Python (FastAPI + SQLite)

When you download this project as a ZIP to run on your local RTX 3060 server, you can continue development directly on our Express backend or easily transition to Python (FastAPI) using the blueprint files provided in this repository.

A parallel Python server skeleton (`server.py`) is already included to jumpstart your transition to Python-based offline adapters!
