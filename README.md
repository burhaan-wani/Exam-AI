# Exam AI

Exam AI is a full-stack application for generating exam question banks from a syllabus, assembling final papers, and evaluating descriptive student answers with LLM-assisted scoring.

## Current Product Shape

### Teacher workflow
1. Register or log in as a teacher.
2. Upload a syllabus file.
3. Upload optional reference material for retrieval-augmented generation.
4. Generate a question bank across extracted units and Bloom levels.
5. Generate a final question paper from the bank.
6. Replace weak questions directly from the final paper view.
7. Share the paper link with students or export it as PDF.

### Student workflow
1. Register or log in as a student.
2. Open a shared paper.
3. Submit descriptive answers.
4. Trigger evaluation.
5. Review detailed per-question results.

## Tech Stack

### Backend
- FastAPI
- MongoDB with Motor
- OpenRouter-backed LLM calls
- LangChain for prompt orchestration and retrieval plumbing
- Chroma for persistent vector storage
- sentence-transformers embeddings
- JWT auth with bcrypt/password hashing

### Frontend
- React 18
- Vite
- Tailwind CSS
- Axios
- React Router v6
- Sonner
- html2pdf.js

## Architecture

```text
React frontend
  -> Axios API client
  -> FastAPI routes
  -> services / chains
  -> MongoDB
  -> OpenRouter LLMs
  -> Chroma persistent vector store for syllabus reference retrieval
```

## Repository Structure

```text
exam-ai/
|-- backend/
|   |-- app/
|   |   |-- chains/
|   |   |-- dependencies/
|   |   |-- models/
|   |   |-- routes/
|   |   |-- services/
|   |   |-- utils/
|   |   |-- config.py
|   |   |-- database.py
|   |   `-- main.py
|   |-- requirements.txt
|   `-- .env.example
|-- frontend/
|   |-- src/
|   |   |-- api/
|   |   |-- components/
|   |   |-- lib/
|   |   `-- pages/
|   |-- package.json
|   |-- vite.config.js
|   `-- tailwind.config.js
|-- API_REFERENCE.md
|-- FEATURES.md
|-- INSTALLATION.md
`-- README.md
```

## Key Backend Modules

- `backend/app/routes/auth.py`: register and login.
- `backend/app/routes/syllabus.py`: teacher-owned syllabus listing and retrieval.
- `backend/app/routes/question_bank.py`: new teacher pipeline endpoints.
- `backend/app/routes/paper.py`: authenticated paper retrieval.
- `backend/app/routes/evaluation.py`: student submission and evaluation endpoints.
- `backend/app/dependencies/auth.py`: JWT verification and role guards.
- `backend/app/services/question_bank_generator.py`: question bank generation with persistent retrieval.
- `backend/app/services/paper_generator.py`: paper selection from the bank.
- `backend/app/services/vector_store.py`: Chroma-backed persistent vector indexing.
- `backend/app/services/answer_evaluator.py`: evaluation orchestration.

## Authentication and Authorization

The backend now enforces JWT authentication and role-based access.

- Teacher endpoints require a valid teacher token.
- Student endpoints require a valid student token.
- Syllabi, papers, and student submissions are scoped server-side.

Use the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

## Current API Surface

### Auth
- `POST /api/auth/register`
- `POST /api/auth/login`

### Teacher workflow
- `POST /api/upload-syllabus`
- `GET /api/syllabus/list`
- `GET /api/syllabus/{syllabus_id}`
- `POST /api/upload-reference-material`
- `GET /api/reference-material`
- `POST /api/generate-question-bank`
- `GET /api/question-bank`
- `POST /api/generate-question-paper`
- `POST /api/review-question`
- `GET /api/final-paper`
- `GET /api/paper/{paper_id}`

### Student workflow
- `POST /api/evaluation/submit`
- `GET /api/evaluation/{answer_id}`
- `POST /api/evaluation/evaluate`
- `GET /api/evaluation/results/{eval_id}`
- `GET /api/evaluation/by-submission/{answer_id}`
- `GET /api/evaluation/by-paper/{paper_id}`

### Utility
- `GET /api/health`

## Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- MongoDB
- OpenRouter API key

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend default URL: `http://localhost:5173`
Backend default URL: `http://localhost:8000`
Swagger docs: `http://localhost:8000/docs`

## Environment Variables

Backend environment variables:

```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=exam_ai
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_MODEL=openai/gpt-oss-120b:free
SECRET_KEY=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=480
CORS_ORIGINS=http://localhost:5173
```

## Current Status

Implemented:
- New teacher question-bank pipeline
- Persistent retrieval store for uploaded reference material
- Backend JWT auth and role enforcement
- Student answer submission and evaluation
- Teacher paper replacement flow
- Frontend PDF export

Still pending:
- Automated tests
- Broader teacher analytics
- LMS integrations
- Mobile app

## Notes

- The legacy blueprint/HITL teacher pipeline has been removed from the application source.
- Retrieval now persists per syllabus instead of being rebuilt fully in memory on each generation request.
- Some older project-summary documents may describe the original implementation history rather than the live code. This README reflects the current codebase.
