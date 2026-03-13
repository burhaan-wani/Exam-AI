# Exam AI API Reference

Base URL: `http://localhost:8000/api`

All protected endpoints require:

```http
Authorization: Bearer <access_token>
```

## Authentication

### POST `/auth/register`
Create a teacher or student account.

```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "password": "securepassword",
  "role": "teacher"
}
```

Response:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": "user-id",
    "name": "Jane Doe",
    "email": "jane@example.com",
    "role": "teacher"
  }
}
```

### POST `/auth/login`
Authenticate and receive a JWT.

## Teacher Workflow Endpoints

All endpoints below require a teacher token.

### POST `/upload-syllabus`
Upload a syllabus file and extract units.

Multipart form:
- `file`: PDF, DOCX, or TXT syllabus

Response:

```json
{
  "id": "syllabus-id",
  "filename": "course_syllabus.pdf",
  "units": ["Unit 1", "Unit 2"],
  "unit_count": 2,
  "created_at": "2026-03-13T12:00:00Z"
}
```

### GET `/syllabus/list`
List the authenticated teacher's syllabi.

### GET `/syllabus/{syllabus_id}`
Get details for a teacher-owned syllabus.

### POST `/upload-reference-material`
Upload and immediately index reference material into the persistent retrieval store.

Multipart form:
- `syllabus_id`
- `file`

Response:

```json
{
  "id": "document-id",
  "syllabus_id": "syllabus-id",
  "file_name": "lecture_notes.pdf",
  "uploaded_at": "2026-03-13T12:15:00Z",
  "chunk_count": 18
}
```

### GET `/reference-material?syllabus_id=...`
List uploaded reference materials for a teacher-owned syllabus.

### POST `/generate-question-bank`
Generate and persist question-bank items for a syllabus.

```json
{
  "syllabus_id": "syllabus-id"
}
```

### GET `/question-bank?syllabus_id=...`
List bank questions. Optional filters:
- `unit`
- `bloom_level`

### POST `/generate-question-paper`
Create a paper from the existing question bank.

```json
{
  "syllabus_id": "syllabus-id",
  "title": "Midterm Examination",
  "sections": [
    { "name": "Section A", "bloom_level": "Remember", "num_questions": 3 },
    { "name": "Section B", "bloom_level": "Apply", "num_questions": 2 }
  ]
}
```

### POST `/review-question`
Replace a final-paper question with a new bank question from the same unit/Bloom bucket.

Multipart form:
- `paper_id`
- `question_number`

### GET `/final-paper?paper_id=...`
Teacher alias for reading a generated paper.

### GET `/paper/{paper_id}`
Read a generated paper by ID. Requires authentication.

## Student Workflow Endpoints

All submission and evaluation endpoints below require a student token unless noted otherwise.

### POST `/evaluation/submit`
Submit answers for a paper.

```json
{
  "paper_id": "paper-id",
  "student_name": "Alice",
  "answers": [
    { "question_number": 1, "answer_text": "Answer text" }
  ]
}
```

### GET `/evaluation/{answer_id}`
Get the authenticated student's own submission.

### POST `/evaluation/evaluate`
Trigger evaluation for the authenticated student's own submission.

```json
{
  "answer_id": "submission-id"
}
```

### GET `/evaluation/results/{eval_id}`
Get the authenticated student's own evaluation result.

### GET `/evaluation/by-submission/{answer_id}`
Get evaluation for the authenticated student's own submission ID.

### GET `/evaluation/by-paper/{paper_id}`
Teacher-only endpoint for listing evaluations for a teacher-owned paper.

## Utility

### GET `/health`
Health check.

## Error Format

```json
{
  "detail": "Error message"
}
```

Common status codes:
- `200` success
- `400` invalid input
- `401` missing/invalid token
- `403` role or ownership violation
- `404` not found
- `500` server error

## Current Workflow Summary

### Teacher
1. Register/login.
2. Upload syllabus.
3. Upload optional reference material.
4. Generate question bank.
5. Generate question paper.
6. Replace questions if needed.
7. Share or export the paper.

### Student
1. Register/login.
2. Open paper.
3. Submit answers.
4. Run evaluation.
5. View results.
