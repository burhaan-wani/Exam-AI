import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests if available
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auth APIs
export const authAPI = {
  register: (data) => apiClient.post('/auth/register', data),
  login: (data) => apiClient.post('/auth/login', data),
}

// Syllabus APIs
export const syllabusAPI = {
  upload: (file, userId = 'anonymous') => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('user_id', userId)
    return apiClient.post('/syllabus/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  list: (userId = 'anonymous') =>
    apiClient.get('/syllabus/list', { params: { user_id: userId } }),
  get: (syllabusId) => apiClient.get(`/syllabus/${syllabusId}`),
}

// Question APIs
export const questionsAPI = {
  createBlueprint: (data) => apiClient.post('/questions/blueprint', data),
  getBlueprint: (blueprintId) =>
    apiClient.get(`/questions/blueprint/${blueprintId}`),
  generate: (data) => apiClient.post('/questions/generate', data),
  listByBlueprint: (blueprintId) =>
    apiClient.get(`/questions/by-blueprint/${blueprintId}`),
}

// HITL APIs
export const hitlAPI = {
  review: (data) => apiClient.post('/hitl/review', data),
  getFeedback: (questionId) =>
    apiClient.get(`/hitl/feedback/${questionId}`),
}

// Paper APIs
export const paperAPI = {
  assemble: (data) => apiClient.post('/paper/assemble', data),
  get: (paperId) => apiClient.get(`/paper/${paperId}`),
  listByBlueprint: (blueprintId) =>
    apiClient.get(`/paper/by-blueprint/${blueprintId}`),
}

// Evaluation APIs
export const evaluationAPI = {
  submitAnswers: (data) => apiClient.post('/evaluation/submit', data),
  getSubmission: (answerId) =>
    apiClient.get(`/evaluation/${answerId}`),
  evaluate: (data) => apiClient.post('/evaluation/evaluate', data),
  getResults: (evalId) =>
    apiClient.get(`/evaluation/results/${evalId}`),
  getResultsBySubmission: (answerId) =>
    apiClient.get(`/evaluation/by-submission/${answerId}`),
  listByPaper: (paperId) =>
    apiClient.get(`/evaluation/by-paper/${paperId}`),
}

// Two-stage Question Bank / Paper APIs
export const questionBankAPI = {
  // New syllabus upload endpoint for the two-stage pipeline
  uploadSyllabus: (file, userId = 'anonymous') => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('user_id', userId)
    return apiClient.post('/upload-syllabus', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  uploadReferenceMaterial: (syllabusId, file) => {
    const formData = new FormData()
    formData.append('syllabus_id', syllabusId)
    formData.append('file', file)
    return apiClient.post('/upload-reference-material', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  generateQuestionBank: (syllabusId) =>
    apiClient.post('/generate-question-bank', { syllabus_id: syllabusId }),

  listQuestionBank: (syllabusId, params = {}) =>
    apiClient.get('/question-bank', {
      params: { syllabus_id: syllabusId, ...params },
    }),

  generateQuestionPaper: (template) =>
    apiClient.post('/generate-question-paper', template),

  reviewQuestionInPaper: (paperId, questionNumber) => {
    const formData = new FormData()
    formData.append('paper_id', paperId)
    formData.append('question_number', String(questionNumber))
    return apiClient.post('/review-question', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  getFinalPaper: (paperId) => apiClient.get('/final-paper', { params: { paper_id: paperId } }),
}

export default apiClient
