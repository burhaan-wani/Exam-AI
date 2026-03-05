# Installation Guide - Exam AI

Complete step-by-step guide to set up and run the Exam AI application.

## Prerequisites

Before starting, ensure you have:

1. **Python 3.9 or higher**
   ```bash
   python --version  # or python3 --version
   ```

2. **Node.js 16 or higher**
   ```bash
   node --version
   npm --version
   ```

3. **MongoDB**
   - Local installation: https://docs.mongodb.com/manual/installation/
   - Or MongoDB Atlas (Cloud): https://www.mongodb.com/cloud/atlas

4. **OpenAI API Key**
   - Get it from: https://platform.openai.com/api-keys
   - Ensure you have sufficient credits/quota

## Quick Start (Recommended)

### For Windows
```bash
cd exam-ai
setup.bat
```

### For macOS/Linux
```bash
cd exam-ai
chmod +x setup.sh
./setup.sh
```

Then follow the instructions in the script output.

---

## Manual Installation

### Step 1: Clone/Prepare the Repository

```bash
cd exam-ai
```

### Step 2: Backend Setup

#### 2.1 Create Virtual Environment

**Windows:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

#### 2.2 Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2.3 Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
# Copy from example
cp .env.example .env
```

Edit `.env` and fill in your settings:

```env
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=exam_ai

# OpenAI Configuration
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4-mini

# JWT Configuration
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=480

# CORS Configuration
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**Important Settings Explanation:**

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` or MongoDB Atlas URL |
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-...` |
| `OPENAI_MODEL` | Model to use | `gpt-4-mini` (or `gpt-4-turbo`) |
| `SECRET_KEY` | JWT signing key | Any random string, 32+ chars recommended |
| `CORS_ORIGINS` | Frontend URL for API access | `http://localhost:5173` during development |

#### 2.4 Verify MongoDB Connection

Make sure MongoDB is running:

**Local MongoDB:**
```bash
# macOS (if installed via Homebrew)
brew services start mongodb-community

# Linux
sudo systemctl start mongod

# Windows (MongoDB Community Server)
# MongoDB should start as a service automatically
# Or from Command Prompt:
net start MongoDB
```

**MongoDB Atlas (Cloud):**
Use connection string like:
```
mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
```

#### 2.5 Start Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```

You should see:
```
Uvicorn running on http://127.0.0.1:8000
```

**API Documentation:** Visit `http://localhost:8000/docs` to see all endpoints

### Step 3: Frontend Setup

#### 3.1 Install Dependencies

In a **new terminal** (keep backend running):

```bash
cd frontend
npm install
```

#### 3.2 Configure Environment (Optional)

Create `.env.local` in the `frontend` directory:

```env
VITE_API_URL=http://localhost:8000/api
```

(This is optional - defaults to localhost:8000)

#### 3.3 Start Development Server

```bash
npm run dev
```

You should see:
```
VITE v5.0.0  ready in XXX ms

➜  Local:   http://localhost:5173/
```

### Step 4: Access the Application

Open your browser and navigate to: **http://localhost:5173**

## First Time Setup - Create Test User

1. Go to **Register** page
2. Create an account (teacher role for testing)
3. Or use test credentials if backend is configured with them

## Troubleshooting

### MongoDB Connection Error

**Error:** `ServerSelectionTimeoutError`

**Solution:**
- Check if MongoDB is running
- Verify connection string in `.env`
- For Atlas, ensure IP whitelist includes your machine's IP (0.0.0.0/0 for development)

### OpenAI API Error

**Error:** `AuthenticationError: Incorrect API key provided`

**Solution:**
- Verify API key in `.env`
- Check API key is active in OpenAI dashboard
- Ensure no extra spaces in the key

### CORS Error in Browser

**Error:** `Access to XMLHttpRequest at 'http://localhost:8000...' blocked by CORS`

**Solution:**
- Add frontend URL to `CORS_ORIGINS` in backend `.env`
- Example: `CORS_ORIGINS=http://localhost:5173`
- Restart backend server

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Change backend port
uvicorn app.main:app --reload --port 8001

# Change frontend port
npm run dev -- --port 5174
```

### Module Not Found Error

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solution:**
```bash
# Make sure you're in the backend directory
cd backend
# And virtual environment is activated
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

### Permission Denied (setup.sh)

**Error:** `Permission denied: ./setup.sh`

**Solution:**
```bash
chmod +x setup.sh
./setup.sh
```

### Rust Compilation Error (Windows)

**Error:** `Cargo, the Rust package manager, is not installed` or `pydantic-core` build fails

**Solution (Choose One):**

**Option A: Install Rust (Recommended)**
1. Download from https://rustup.rs/
2. Run the installer and follow prompts
3. Restart your terminal
4. Retry: `pip install -r requirements.txt`

**Option B: Use Pre-built Wheels** (Already done in latest requirements.txt)
- Just reinstall: `pip install -r requirements.txt`

**Option C: Use Anaconda**
```bash
conda create -n exam-ai python=3.9
conda activate exam-ai
cd backend
pip install -r requirements.txt
```

## Production Deployment

### Backend Deployment

1. **Update `.env`:**
   ```env
   SECRET_KEY=<very-long-random-string>
   CORS_ORIGINS=https://yourdomain.com
   ```

2. **Use production ASGI server:**
   ```bash
   pip install gunicorn
   gunicorn app.main:app --workers 4 --bind 0.0.0.0:8000
   ```

3. **Use external MongoDB:**
   ```env
   MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/
   ```

### Frontend Deployment

1. **Build for production:**
   ```bash
   npm run build
   ```

2. **Deploy `dist/` folder** to:
   - Vercel, Netlify, AWS S3, etc.

3. **Update API URL:**
   Create `.env.production`:
   ```env
   VITE_API_URL=https://api.yourdomain.com
   ```

## Docker Support (Optional)

### Docker Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_DATABASE: exam_ai

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - mongodb
    environment:
      MONGODB_URL: mongodb://mongodb:27017
      OPENAI_API_KEY: ${OPENAI_API_KEY}

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
```

Run with:
```bash
docker-compose up
```

## Next Steps

1. **Create a syllabus** - Upload your first course syllabus
2. **Configure Bloom levels** - Set up question difficulty
3. **Generate questions** - Create exam questions with AI
4. **Review & refine** - Use HITL to improve questions
5. **Share paper** - Generate and share with students
6. **Evaluate answers** - Let AI evaluate student responses

## Getting Help

- **API Documentation:** http://localhost:8000/docs
- **GitHub Issues:** [Create an issue]
- **Documentation:** See README.md

## Support Links

- OpenAI Documentation: https://platform.openai.com/docs/
- MongoDB Docs: https://docs.mongodb.com/
- FastAPI Docs: https://fastapi.tiangolo.com/
- React Docs: https://react.dev/
