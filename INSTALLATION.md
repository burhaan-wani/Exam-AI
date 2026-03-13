# Installation Guide - Exam AI

This guide sets up the current Exam AI application, which uses the question-bank teacher workflow, OpenRouter-backed LLM calls, MongoDB, and a React frontend.

## Prerequisites

Install these first:

1. Python 3.9+
2. Node.js 16+
3. MongoDB (local or Atlas)
4. OpenRouter API key: https://openrouter.ai/keys

Helpful checks:

```bash
python --version
node --version
npm --version
```

## Quick Start

### Windows
```bash
cd exam-ai
setup.bat
```

### macOS / Linux
```bash
cd exam-ai
chmod +x setup.sh
./setup.sh
```

The setup scripts prepare dependencies and copy the backend environment file if needed.

## Manual Installation

### 1. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Windows activation is:

```bash
venv\Scripts\activate
```

### 2. Configure backend environment

Edit `backend/.env`:

```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=exam_ai
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_MODEL=openai/gpt-oss-120b:free
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=480
CORS_ORIGINS=http://localhost:5173
```

Variable notes:

| Variable | Purpose |
|----------|---------|
| `MONGODB_URL` | MongoDB connection string |
| `DATABASE_NAME` | Database name |
| `OPENROUTER_API_KEY` | API key for chat model access via OpenRouter |
| `OPENROUTER_MODEL` | Chat model identifier |
| `SECRET_KEY` | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime |
| `CORS_ORIGINS` | Allowed frontend origins |

### 3. Start backend

```bash
uvicorn app.main:app --reload --port 8000
```

Backend URLs:
- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

### 4. Frontend setup

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Optional frontend env file:

```env
VITE_API_URL=http://localhost:8000/api
```

Frontend URL:
- `http://localhost:5173`

## First Run Workflow

### Teacher
1. Register as a teacher.
2. Upload a syllabus.
3. Upload optional reference material.
4. Generate a question bank.
5. Generate a paper.
6. Replace questions if needed.
7. Share/export the paper.

### Student
1. Register as a student.
2. Open a shared paper.
3. Submit answers.
4. Trigger evaluation.
5. Review results.

## Troubleshooting

### MongoDB connection errors
- Make sure MongoDB is running locally, or that your Atlas connection string is valid.
- Confirm `MONGODB_URL` in `backend/.env`.

### OpenRouter authentication errors
- Confirm `OPENROUTER_API_KEY` is set correctly.
- Make sure the key has available credits/access.
- Confirm `OPENROUTER_MODEL` is a chat model, not an embedding model.

### CORS errors
- Add the frontend URL to `CORS_ORIGINS`.
- Restart the backend after changing `.env`.

### Python or npm not found in the terminal
If the tools are installed but not found, fix your shell `PATH` or run them by absolute path. Restart the terminal after changing PATH.

### Port already in use
Use alternate ports if needed:

```bash
uvicorn app.main:app --reload --port 8001
npm run dev -- --port 5174
```

## Production Notes

### Backend
- Use a strong `SECRET_KEY`.
- Set `CORS_ORIGINS` to your deployed frontend URL.
- Point `MONGODB_URL` to production MongoDB.
- Run behind a production ASGI server such as Gunicorn/Uvicorn workers.

### Frontend
- Build with:

```bash
npm run build
```

- Set `VITE_API_URL` to your deployed backend.

## Current Implementation Notes

- The legacy teacher blueprint/HITL flow has been removed.
- The teacher workflow now runs through the question bank pipeline only.
- Retrieval persists per syllabus using a Chroma-backed vector store.
- Backend auth and role checks are enforced server-side.
- Frontend PDF export is implemented.
