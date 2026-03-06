import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'sonner'
import ProtectedRoute, { TeacherRoute, StudentRoute } from './components/ProtectedRoute'
import Layout from './components/layout/Layout'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import TeacherDashboard from './pages/teacher/TeacherDashboard'
import SyllabusUpload from './pages/teacher/SyllabusUpload'
import BloomConfig from './pages/teacher/BloomConfig'
import QuestionGeneration from './pages/teacher/QuestionGeneration'
import HITLReview from './pages/teacher/HITLReview'
import QuestionPaperView from './pages/teacher/QuestionPaperView'
import QuestionBankPage from './pages/teacher/QuestionBankPage'
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
          {/* Teacher routes */}
          <Route
            path="dashboard"
            element={
              <TeacherRoute>
                <TeacherDashboard />
              </TeacherRoute>
            }
          />
          <Route
            path="upload-syllabus"
            element={
              <TeacherRoute>
                <SyllabusUpload />
              </TeacherRoute>
            }
          />
          <Route
            path="configure-bloom/:syllabusId"
            element={
              <TeacherRoute>
                <BloomConfig />
              </TeacherRoute>
            }
          />
          <Route
            path="generate-questions/:blueprintId"
            element={
              <TeacherRoute>
                <QuestionGeneration />
              </TeacherRoute>
            }
          />
          <Route
            path="review-questions/:blueprintId"
            element={
              <TeacherRoute>
                <HITLReview />
              </TeacherRoute>
            }
          />
          <Route
            path="question-paper/:paperId"
            element={
              <TeacherRoute>
                <QuestionPaperView />
              </TeacherRoute>
            }
          />
          <Route
            path="question-bank/:syllabusId"
            element={
              <TeacherRoute>
                <QuestionBankPage />
              </TeacherRoute>
            }
          />

          {/* Student routes */}
          <Route
            path="submit-answers/:paperId"
            element={
              <StudentRoute>
                <StudentAnswerSubmission />
              </StudentRoute>
            }
          />
          <Route
            path="evaluation-results/:evalId"
            element={
              <StudentRoute>
                <EvaluationResults />
              </StudentRoute>
            }
          />

          <Route index element={<Navigate to="/dashboard" replace />} />
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>

      <Toaster position="top-right" />
    </Router>
  )
}

export default App
