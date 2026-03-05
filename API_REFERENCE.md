# Exam AI - API Reference

Complete API documentation for all endpoints.

**Base URL:** `http://localhost:8000/api`

## Authentication

All protected endpoints require a JWT token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

---

## Authentication Endpoints

### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword",
  "role": "teacher"  // or "student"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "teacher"
  }
}
```

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "securepassword"
}
```

**Response:** Same as register

---

## Syllabus Endpoints

### Upload Syllabus
```http
POST /syllabus/upload
Content-Type: multipart/form-data

file: <PDF/DOCX/TXT file>
user_id: "507f1f77bcf86cd799439011"
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439012",
  "filename": "course_syllabus.pdf",
  "topic_count": 12,
  "topics": [
    {
      "name": "Introduction to Programming",
      "unit": "Unit 1",
      "subtopics": ["Variables", "Data Types", "Operators"]
    }
  ]
}
```

### List Syllabi
```http
GET /syllabus/list?user_id=507f1f77bcf86cd799439011
```

**Response:**
```json
[
  {
    "id": "507f1f77bcf86cd799439012",
    "filename": "course_syllabus.pdf",
    "topic_count": 12,
    "created_at": "2024-01-15T10:30:00"
  }
]
```

### Get Syllabus Details
```http
GET /syllabus/{syllabus_id}
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439012",
  "user_id": "507f1f77bcf86cd799439011",
  "filename": "course_syllabus.pdf",
  "raw_text": "...",
  "topics": [...],
  "created_at": "2024-01-15T10:30:00"
}
```

---

## Question Blueprint Endpoints

### Create Blueprint
```http
POST /questions/blueprint
Content-Type: application/json

{
  "syllabus_id": "507f1f77bcf86cd799439012",
  "exam_title": "Final Examination",
  "total_marks": 100,
  "duration_minutes": 180,
  "configs": [
    {
      "topic": "Introduction to Programming",
      "bloom_level": "Remember",
      "num_questions": 2,
      "marks_per_question": 5,
      "difficulty": "easy"
    },
    {
      "topic": "Data Structures",
      "bloom_level": "Apply",
      "num_questions": 3,
      "marks_per_question": 10,
      "difficulty": "medium"
    }
  ]
}
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439013",
  "syllabus_id": "507f1f77bcf86cd799439012",
  "exam_title": "Final Examination",
  "total_marks": 100,
  "duration_minutes": 180,
  "configs": [...],
  "created_at": "2024-01-15T10:35:00"
}
```

### Get Blueprint
```http
GET /questions/blueprint/{blueprint_id}
```

**Response:** Same as create response

---

## Question Generation Endpoints

### Generate Questions
```http
POST /questions/generate
Content-Type: application/json

{
  "blueprint_id": "507f1f77bcf86cd799439013"
}
```

**Response:**
```json
{
  "count": 5,
  "questions": [
    {
      "id": "507f1f77bcf86cd799439014",
      "topic": "Introduction to Programming",
      "bloom_level": "Remember",
      "difficulty": "easy",
      "question_text": "What is a variable?",
      "marks": 5,
      "sub_questions": [],
      "model_answer": "A variable is a named storage location...",
      "status": "pending",
      "created_at": "2024-01-15T10:40:00"
    }
  ]
}
```

### List Questions by Blueprint
```http
GET /questions/by-blueprint/{blueprint_id}
```

**Response:** Array of questions (same format as generate)

---

## HITL Review Endpoints

### Review Question
```http
POST /hitl/review
Content-Type: application/json

{
  "question_id": "507f1f77bcf86cd799439014",
  "action": "approved",  // or "rejected", "modified", "regenerate"
  "modified_text": "New question text (for modified action)",
  "feedback_note": "Please improve clarity (for regenerate action)"
}
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439014",
  "topic": "Introduction to Programming",
  "bloom_level": "Remember",
  "question_text": "What is a variable?",
  "status": "approved",
  "marks": 5,
  "model_answer": "...",
  "created_at": "2024-01-15T10:40:00"
}
```

### Get Feedback History
```http
GET /hitl/feedback/{question_id}
```

**Response:**
```json
[
  {
    "id": "507f1f77bcf86cd799439015",
    "question_id": "507f1f77bcf86cd799439014",
    "action": "regenerate",
    "modified_text": null,
    "feedback_note": "Please improve clarity",
    "created_at": "2024-01-15T10:50:00"
  },
  {
    "id": "507f1f77bcf86cd799439016",
    "question_id": "507f1f77bcf86cd799439014",
    "action": "approved",
    "modified_text": null,
    "feedback_note": null,
    "created_at": "2024-01-15T11:00:00"
  }
]
```

---

## Question Paper Endpoints

### Assemble Paper
```http
POST /paper/assemble
Content-Type: application/json

{
  "blueprint_id": "507f1f77bcf86cd799439013"
}
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439017",
  "syllabus_id": "507f1f77bcf86cd799439012",
  "blueprint_id": "507f1f77bcf86cd799439013",
  "exam_title": "Final Examination",
  "total_marks": 100,
  "duration_minutes": 180,
  "questions": [
    {
      "question_number": 1,
      "question_text": "What is a variable?",
      "sub_questions": [],
      "marks": 5,
      "bloom_level": "Remember",
      "topic": "Introduction to Programming"
    }
  ],
  "created_at": "2024-01-15T11:05:00"
}
```

### Get Paper
```http
GET /paper/{paper_id}
```

**Response:** Same as assemble response

### List Papers by Blueprint
```http
GET /paper/by-blueprint/{blueprint_id}
```

**Response:** Array of papers

---

## Student Answer Endpoints

### Submit Answers
```http
POST /evaluation/submit
Content-Type: application/json

{
  "paper_id": "507f1f77bcf86cd799439017",
  "student_name": "Alice Johnson",
  "answers": [
    {
      "question_number": 1,
      "answer_text": "A variable is a named storage location that holds a value"
    },
    {
      "question_number": 2,
      "answer_text": "The three main data types are..."
    }
  ]
}
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439018",
  "paper_id": "507f1f77bcf86cd799439017",
  "student_name": "Alice Johnson",
  "answers": [...],
  "submitted_at": "2024-01-15T11:30:00"
}
```

### Get Submission
```http
GET /evaluation/{answer_id}
```

**Response:** Same as submit response

---

## Evaluation Endpoints

### Evaluate Answers
```http
POST /evaluation/evaluate
Content-Type: application/json

{
  "answer_id": "507f1f77bcf86cd799439018"
}
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439019",
  "answer_id": "507f1f77bcf86cd799439018",
  "paper_id": "507f1f77bcf86cd799439017",
  "student_name": "Alice Johnson",
  "question_scores": [
    {
      "question_number": 1,
      "max_marks": 5,
      "awarded_marks": 4.5,
      "semantic_similarity": 0.92,
      "completeness": 0.85,
      "bloom_alignment": 0.88,
      "reasoning": "Answer correctly defines variable with good clarity",
      "feedback": "Very good! Consider mentioning scope in future answers."
    }
  ],
  "total_marks": 85.5,
  "max_marks": 100,
  "percentage": 85.5,
  "overall_feedback": "Overall Grade: Very Good (85.5%). Focus on improving: Q3, Q5.",
  "evaluated_at": "2024-01-15T11:35:00"
}
```

### Get Evaluation Results
```http
GET /evaluation/results/{eval_id}
```

**Response:** Same as evaluate response

### Get Results by Submission
```http
GET /evaluation/by-submission/{answer_id}
```

**Response:** Same as evaluate response

### List Evaluations by Paper
```http
GET /evaluation/by-paper/{paper_id}
```

**Response:** Array of evaluation results

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (invalid input) |
| 401 | Unauthorized (missing/invalid token) |
| 404 | Not Found |
| 500 | Server Error |

### Example Error Response

```json
{
  "detail": "Blueprint not found"
}
```

---

## Rate Limiting

- No strict rate limits during development
- For production, implement API rate limiting

---

## Data Types

### BloomLevel
```
"Remember" | "Understand" | "Apply" | "Analyze" | "Evaluate" | "Create"
```

### Difficulty
```
"easy" | "medium" | "hard"
```

### QuestionStatus
```
"pending" | "approved" | "rejected" | "modified" | "regenerate"
```

### UserRole
```
"teacher" | "student"
```

---

## Example Workflows

### Complete Teacher Workflow

1. **Register/Login**
   ```
   POST /auth/register → get access_token
   ```

2. **Upload Syllabus**
   ```
   POST /syllabus/upload → get syllabus_id
   ```

3. **Create Blueprint**
   ```
   POST /questions/blueprint → get blueprint_id
   ```

4. **Generate Questions**
   ```
   POST /questions/generate → get questions
   ```

5. **Review Questions**
   ```
   POST /hitl/review → Update question status
   ```

6. **Assemble Paper**
   ```
   POST /paper/assemble → get paper_id
   ```

### Complete Student Workflow

1. **Register/Login**
   ```
   POST /auth/register (role: "student") → get access_token
   ```

2. **View Paper**
   ```
   GET /paper/{paper_id}
   ```

3. **Submit Answers**
   ```
   POST /evaluation/submit → get answer_id
   ```

4. **Get Evaluation**
   ```
   GET /evaluation/by-submission/{answer_id}
   ```

---

## Testing with cURL

### Register
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "test123",
    "role": "teacher"
  }'
```

### Upload Syllabus
```bash
curl -X POST http://localhost:8000/api/syllabus/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@syllabus.pdf" \
  -F "user_id=USER_ID"
```

### Create Blueprint
```bash
curl -X POST http://localhost:8000/api/questions/blueprint \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

---

## Additional Resources

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json
