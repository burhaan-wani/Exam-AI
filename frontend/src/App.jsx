import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'sonner'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/layout/Layout'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import TeacherDashboard from './pages/teacher/TeacherDashboard'
import SyllabusUpload from './pages/teacher/SyllabusUpload'
import BloomConfig from './pages/teacher/BloomConfig'
import QuestionGeneration from './pages/teacher/QuestionGeneration'
import HITLReview from './pages/teacher/HITLReview'
import QuestionPaperView from './pages/teacher/QuestionPaperView'
import StudentAnswerSubmission from './pages/student/StudentAnswerSubmission'
import EvaluationResults from './pages/student/EvaluationResults'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="dashboard" element={<TeacherDashboard />} />
          <Route path="upload-syllabus" element={<SyllabusUpload />} />
          <Route path="configure-bloom/:syllabusId" element={<BloomConfig />} />
          <Route path="generate-questions/:blueprintId" element={<QuestionGeneration />} />
          <Route path="review-questions/:blueprintId" element={<HITLReview />} />
          <Route path="question-paper/:paperId" element={<QuestionPaperView />} />
          <Route path="submit-answers/:paperId" element={<StudentAnswerSubmission />} />
          <Route path="evaluation-results/:evalId" element={<EvaluationResults />} />
          <Route index element={<Navigate to="/dashboard" replace />} />
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>

      <Toaster position="top-right" />
    </Router>
  )
}

export default App
