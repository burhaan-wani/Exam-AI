import { Navigate } from 'react-router-dom'

const getCurrentUser = () => {
  try {
    const raw = localStorage.getItem('user')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('access_token')

  if (!token) {
    return <Navigate to="/login" replace />
  }

  return children
}

export const TeacherRoute = ({ children }) => {
  const token = localStorage.getItem('access_token')
  const user = getCurrentUser()

  if (!token || !user) {
    return <Navigate to="/login" replace />
  }

  if (user.role !== 'teacher') {
    return <Navigate to="/submit-answers/unauthorized" replace />
  }

  return children
}

export const StudentRoute = ({ children }) => {
  const token = localStorage.getItem('access_token')
  const user = getCurrentUser()

  if (!token || !user) {
    return <Navigate to="/login" replace />
  }

  if (user.role !== 'student') {
    return <Navigate to="/dashboard" replace />
  }

  return children
}

export default ProtectedRoute
