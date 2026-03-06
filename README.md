# Exam AI - Question Paper Generation & Answer Evaluation

A full-stack web application that automates exam question paper generation using Bloom's Taxonomy and evaluates student descriptive answers using LLM-based rubric scoring.

## Features

### For Teachers
- **Upload Syllabus**: Support for PDF, DOCX, and TXT files
- **Topic Extraction**: AI-powered automatic topic extraction
- **Bloom's Taxonomy Configuration**: Map topics to cognitive levels (Remember → Create)
- **Question Generation**: Generate exam questions using OpenAI GPT models
- **HITL Review Loop**: Approve, reject, or request changes to generated questions
- **Question Paper Assembly**: Create A4-formatted question papers
- **Marks Allocation**: Automatic intelligent mark distribution

### For Students
- **Answer Submission**: Submit descriptive answers for each question
- **AI-Based Evaluation**: LLM-powered rubric scoring
- **Detailed Feedback**: Receive marks, feedback, and scoring rationale
- **Performance Analytics**: View semantic similarity, completeness, and Bloom alignment scores

## Tech Stack

### Backend
- **Framework**: Python FastAPI
- **Database**: MongoDB (with Motor async driver)
- **LLM Integration**: LangChain + OpenAI GPT-4
- **Authentication**: JWT tokens with bcrypt password hashing
- **File Processing**: PyPDF2 for PDFs, python-docx for DOCX files

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: TailwindCSS
- **API Client**: Axios
- **Routing**: React Router v6
- **Notifications**: Sonner
- **Icons**: Lucide React

## Project Structure

```
exam-ai/
├── backend/
│   ├── app/
│   │   ├── routes/           # API endpoints
│   │   ├── services/         # Business logic
│   │   ├── chains/           # LangChain pipelines
│   │   ├── models/           # Pydantic schemas
│   │   ├── utils/            # Helper functions
│   │   ├── config.py         # Settings
│   │   ├── database.py       # MongoDB connection
│   │   └── main.py           # FastAPI app
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/            # React pages
│   │   ├── components/       # Reusable UI components
│   │   ├── api/              # API client
│   │   ├── lib/              # Utilities
│   │   ├── hooks/            # Custom React hooks
│   │   └── App.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 16+
- MongoDB (local or Atlas)
- OpenAI API key

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file** (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and update:
   - `MONGODB_URL`: Your MongoDB connection string
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `SECRET_KEY`: A strong random string for JWT

5. **Run the backend**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   Backend will be available at `http://localhost:8000`
   API docs: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Create `.env` file** (optional, defaults to localhost):
   ```bash
   echo "VITE_API_URL=http://localhost:8000/api" > .env.local
   ```

4. **Run development server**:
   ```bash
   npm run dev
   ```

   Frontend will be available at `http://localhost:5173`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token

### Syllabus Management
- `POST /api/syllabus/upload` - Upload syllabus file
- `GET /api/syllabus/list` - List user's syllabi
- `GET /api/syllabus/{id}` - Get syllabus details

### Question Generation
- `POST /api/questions/blueprint` - Create exam blueprint
- `GET /api/questions/blueprint/{id}` - Get blueprint
- `POST /api/questions/generate` - Generate questions using LLM
- `GET /api/questions/by-blueprint/{id}` - List questions for blueprint

### HITL Review
- `POST /api/hitl/review` - Submit question review action
- `GET /api/hitl/feedback/{id}` - Get feedback history

### Question Paper
- `POST /api/paper/assemble` - Assemble final question paper
- `GET /api/paper/{id}` - Get paper details
- `GET /api/paper/by-blueprint/{id}` - List papers for blueprint

### Answer Evaluation
- `POST /api/evaluation/submit` - Submit student answers
- `GET /api/evaluation/{id}` - Get submission details
- `POST /api/evaluation/evaluate` - Evaluate answers using LLM
- `GET /api/evaluation/results/{id}` - Get evaluation results
- `GET /api/evaluation/by-paper/{id}` - List evaluations for paper

## Database Collections

- **users**: User accounts with roles (teacher/student)
- **syllabus**: Uploaded syllabi and extracted topics
- **question_blueprint**: Exam configurations with Bloom levels
- **generated_questions**: Questions created by LLM
- **hitl_feedback**: Teacher review actions and feedback
- **final_question_paper**: Assembled question papers
- **student_answers**: Student submissions
- **evaluation_results**: AI evaluation results with marks and feedback

## Workflow

### Teacher Workflow
1. **Upload Syllabus** → Topics are automatically extracted
2. **Configure Bloom Levels** → Define cognitive levels per topic
3. **Generate Questions** → LLM creates questions based on config
4. **HITL Review** → Approve, reject, or request changes
5. **Assemble Paper** → Create final A4-formatted question paper
6. **Share with Students** → Provide link for answer submission

### Student Workflow
1. **Receive Paper Link** → Access question paper
2. **Submit Answers** → Write descriptive answers
3. **AI Evaluation** → System evaluates against model answers
4. **View Results** → Check marks, feedback, and analytics

## Bloom's Taxonomy Levels

1. **Remember**: Recall facts and basic concepts
2. **Understand**: Explain ideas or concepts
3. **Apply**: Use information in new situations
4. **Analyze**: Draw connections and break into parts
5. **Evaluate**: Make judgments and justify decisions
6. **Create**: Produce new or original work

## LangChain Integration

The system uses LangChain for orchestrating complex LLM workflows:

- **Generation Chain**: Creates Bloom-aligned questions
- **Refinement Chain**: Refines questions based on HITL feedback
- **Evaluation Chain**: Scores student answers using rubric extraction and semantic analysis

## Evaluation Metrics

Student answers are evaluated on:
- **Semantic Similarity**: How well the answer matches the model answer
- **Completeness**: How many key points from model answer are covered
- **Bloom Alignment**: Does the answer demonstrate the expected cognitive level?
- **Logic & Reasoning**: Is the answer well-structured and logically sound?

## Configuration

### Environment Variables (Backend)

```
MONGODB_URL            # MongoDB connection URI
DATABASE_NAME          # Database name (default: exam_ai)
OPENROUTER_API_KEY     # OpenRouter API key (https://openrouter.ai/keys)
OPENROUTER_MODEL       # Chat model to use via OpenRouter (e.g., openai/gpt-oss-120b:free)
SECRET_KEY             # JWT secret key
ACCESS_TOKEN_EXPIRE_MINUTES  # Token expiry (default: 480)
CORS_ORIGINS           # Comma-separated CORS origins (e.g., http://localhost:5173)
```

## Common Issues

### MongoDB Connection Error
Ensure MongoDB is running:
```bash
# For local MongoDB
mongod

# For MongoDB Atlas, update the connection string in .env
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
```

### OpenAI API Key Issues
- Verify your API key is valid in OpenAI dashboard
- Check API quotas and billing
- Ensure the model specified exists (e.g., `gpt-4-mini`)

### CORS Errors
Update `CORS_ORIGINS` in `.env` to include your frontend URL

## Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm run test
```

### Build for Production

**Frontend**:
```bash
cd frontend
npm run build  # Creates dist/ folder
```

**Backend**:
```bash
# Use a production ASGI server
gunicorn app.main:app --workers 4
```

## Future Enhancements

- [ ] PDF export for question papers
- [ ] Student answer plagiarism detection
- [ ] Question bank management and versioning
- [ ] Analytics dashboard for educators
- [ ] Multiple language support
- [ ] Mobile app for answer submission
- [ ] Integration with LMS platforms

## License

MIT License - feel free to use and modify

## Support

For issues or questions, please open an issue in the repository.

---

**Built with ❤️ using FastAPI, React, and AI**
