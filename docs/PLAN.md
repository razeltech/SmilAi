# SmilAI: High-Performance Architecture Plan
## Enterprise-Grade RAG Pipeline & Andhra Pradesh Board Integration

This document serves as the official roadmap and architectural design specification for **SmilAI (Virtual Teacher Platform)**. It has been prepared by the Senior AI Architect and Developer to ensure performance, stability, and scale.

---

## 1. High-Performance Architecture for 10,000+ PDFs (50,000+ Pages)

To achieve lightning-fast reading speeds on over 10,000+ textbook chapters and up to 50,000+ pages of academic syllabus, we implement a **Hierarchical Sparse-Dense Retrieval & Pre-Clustered Ingestion** architecture.

```
                   +------------------------+
                   |  10k+ PDFs Ingestion   |
                   +------------------------+
                               |
                               v
                     [Document Pre-Processor]
                               |
            +------------------+------------------+
            |                                     |
            v                                     v
  [Hierarchical Chunking]                [Metadata Clustering]
  - Parents: 2000-char chapters          - Class Range (Nursery-12)
  - Children: 400-char concepts          - School Medium (Telugu/Eng)
            |                                     |
            v                                     v
+------------------------+              +------------------------+
|   Hierarchical Index   |              | Metadata Routing Index |
|  - TF-IDF Sparse Index | <==========> |  - Direct Hash Match   |
|  - Embedding Vectors   |   Filters    |  - Grade/Subject Index |
+------------------------+              +------------------------+
            |                                     |
            +------------------+------------------+
                               |
                               v
                    [Re-ranking & Synthesis]
                    - Chunk Cache (Local/In-Memory)
                    - LLM Grounding Context
```

### Key Pillars of the Ingestion & Retrieval Engine:
1. **Hierarchical Parent-Child Chunking**:
   - **Parent Chunks (Large, 2000-3000 chars)**: Stores complete chapters or syllabus sections to maintain full pedagogical context.
   - **Child Chunks (Small, 300-500 chars)**: Represents individual mathematical definitions, historical facts, or code functions. 
   - **Search execution**: We query against small Child Chunks for rapid similarity matching, but retrieve the parent chunk's full text for the LLM to read. This eliminates fragmented, out-of-context teaching answers.

2. **Metadata-Guided Sub-Space Indexing (Syllabus Routing)**:
   - Instead of scanning all 50,000 pages of text simultaneously, the search space is immediately pruned using structured metadata (e.g., `Class 10 -> SSC Board -> Physical Science`).
   - This narrows down the query range from 100,000 candidate chunks to less than 100 candidate chunks in `O(1)` time before any search is executed, delivering `< 10ms` lookup speeds.

3. **Hybrid Search System (TF-IDF Sparse + Embeddings Dense)**:
   - High-speed lexical search matching (BM25/TF-IDF) tracks rare school terms, formulas, and Telugu vocabulary (e.g., *Nishabdam*, *Balachandrudu*).
   - Local, pre-tokenized index trees are stored as structured collections in the local JSON storage, enabling instantly serializable search profiles.

4. **Multi-Format Ingestion System**:
   - Pluggable loaders support direct translation of HTML, PDF text layers, Excel formulas/data grids, Word files (`.docx`), and C++/Python codeblocks.

---

## 2. Andhra Pradesh (AP) Education System Curricular Alignment

SmilAI is customized to fit both Andhra Pradesh Government (AP SCERT / SSC Board) and Private (CBSE/ICSE/State Board) school structures.

### Grade Range Integration (Pre-Primary & 1st to 12th Class)
We model classes into five distinct bands:
1. **Pre-Primary**: Nursery, Lower Kindergarten (LKG), Upper Kindergarten (UKG).
2. **Primary School**: 1st Class, 2nd Class, 3rd Class, 4th Class, and 5th Class.
3. **Upper Primary**: 6th Class, 7th Class, and 8th Class.
4. **High School (SSC)**: 9th Class, 10th Class (Andhra Pradesh SSC Board Examination syllabus).
5. **Higher Secondary / Intermediate**: Junior Inter (11th Class), Senior Inter (12th Class) with M.Bi.C / H.E.C / M.P.C course branches.

### Localized Subject Seeds & Telugu Medium Support
- **Telugu (First Language)**: Focuses on Telugu grammar, literature, and morals (Vemana Shatakam, Sumati Shatakam).
- **Physical Science & Biological Science**: Tailored to AP Board Class 10 State text-books.
- **Social Studies**: Tailored to state history, Indian geography, and regional AP administrative divisions.
- **Mathematics**: Structured around coordinate geometry, trigonometry, and quadratic progressions.

---

## 3. Implementation Status and Zip Export Readiness

We are systematically addressing issues step-by-step:

- [x] **UI Clean-up**: Remove developer/Ollama system warnings ("Disk Optimization Tip") from public student/teacher views to maintain pristine educational atmosphere.
- [x] **Remove AI Sparkles**: Ensure no sparkles icons or flashy gradients are used. Clean, professional Teal and Slate palette representing AP academic portals.
- [ ] **AP Curriculum & Grade Seed**: Re-write `db.ts` to populate all Nursery-UKG & Classes 1-12 grade-bands and AP SCERT subjects.
- [ ] **Extend File Ingestors**: Update `handleFileChange` in the teacher view to support `.pdf`, `.docx`, `.xlsx`, and `.html` formats with high-fidelity client-side structural parsers.
- [ ] **Mic Speech Recognition Fix**: Introduce detailed error state handlers inside `StudentDashboard.tsx` to handle browser frame sandboxes (Iframe permission alerts).
- [ ] **Zip Readiness**: After running successful lints and compiling the application cleanly, the project will be fully ready for ZIP export in AI Studio settings.
