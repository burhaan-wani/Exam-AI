# Exam AI Features Overview

## Core Product Features

### Teacher question-bank workflow
- Upload syllabus files in PDF, DOCX, or TXT format.
- Extract units/topics with an LLM.
- Upload optional course material for retrieval-augmented generation.
- Persist reference embeddings per syllabus in a Chroma vector store.
- Generate a structured question bank across Bloom levels.
- Build a final question paper from the question bank.
- Replace individual paper questions directly from the final review screen.
- Export the final paper as PDF from the frontend.

### Student answer workflow
- Open a generated paper.
- Submit descriptive answers.
- Trigger LLM-assisted evaluation.
- View total score, per-question feedback, and scoring metrics.

## AI and Retrieval Features

### LLM usage
- OpenRouter-backed chat models are used for:
  - syllabus topic extraction
  - question-bank generation
  - final paper selection
  - rubric extraction
  - answer evaluation

### Retrieval-augmented generation
- Uploaded reference materials are stored in MongoDB.
- Extracted text is indexed into a persistent Chroma vector store per syllabus.
- Question-bank generation retrieves relevant chunks by unit before prompting the model.

### Evaluation metrics
- Semantic similarity
- Completeness
- Bloom alignment
- Reasoning and feedback generation

## Security Features

### Authentication
- JWT-based authentication
- Password hashing with bcrypt/passlib
- Backend enforcement of auth on protected routes

### Authorization
- Teacher-only syllabus and question-bank routes
- Student-only answer submission/evaluation routes
- Server-side ownership checks for syllabi, papers, submissions, and results

## Frontend Features

### Teacher UI
- Dashboard centered on the new question-bank workflow
- Syllabus upload screen with optional reference material upload
- Question bank management and generation flow
- Final paper view with replace-question actions
- PDF export and share-link support

### Student UI
- Answer submission interface
- Results page with question-wise score cards

## Current Status Table

| Feature | Status | Notes |
|---------|--------|-------|
| Syllabus upload | Ready | PDF, DOCX, TXT |
| Unit extraction | Ready | LLM-based |
| Reference material upload | Ready | Indexed into persistent retrieval store |
| Persistent RAG | Ready | Chroma-backed per syllabus |
| Question bank generation | Ready | New teacher pipeline |
| Final paper generation | Ready | From question bank |
| Question replacement | Ready | Teacher final review action |
| PDF export | Ready | Frontend export via html2pdf.js |
| Student submission | Ready | Authenticated student flow |
| AI evaluation | Ready | Rubric + scoring prompt |
| Backend auth enforcement | Ready | JWT + role checks |
| Automated tests | Pending | Not added yet |
| Analytics dashboard | Planned | Future work |
| LMS integration | Planned | Future work |
| Mobile app | Planned | Future work |

## Architecture Notes

The current application no longer includes the legacy blueprint/HITL teacher pipeline. The active teacher flow is:

```text
Upload syllabus
-> Upload reference material (optional)
-> Generate question bank
-> Generate paper
-> Replace questions if needed
-> Share/export paper
```

Student flow:

```text
Open paper
-> Submit answers
-> Evaluate
-> View results
```

## Known Remaining Gaps
- No automated test suite yet.
- No teacher analytics/reporting UI yet.
- Retrieval is persistent, but operational tooling for reindex/rebuild is still minimal.
- Documentation now reflects current code, but older historical summary files may still be archival rather than authoritative.
