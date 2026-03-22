import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const authAPI = {
  register: (data) => apiClient.post('/auth/register', data),
  login: (data) => apiClient.post('/auth/login', data),
}

export const syllabusAPI = {
  list: (userId = 'anonymous') =>
    apiClient.get('/syllabus/list', { params: { user_id: userId } }),
  get: (syllabusId) => apiClient.get(`/syllabus/${syllabusId}`),
}

export const paperAPI = {
  get: (paperId) => apiClient.get(`/paper/${paperId}`),
}

export const evaluationAPI = {
  submitAnswers: (data) => apiClient.post('/evaluation/submit', data),
  getSubmission: (answerId) => apiClient.get(`/evaluation/${answerId}`),
  evaluate: (data) => apiClient.post('/evaluation/evaluate', data),
  getResults: (evalId) => apiClient.get(`/evaluation/results/${evalId}`),
  getResultsBySubmission: (answerId) =>
    apiClient.get(`/evaluation/by-submission/${answerId}`),
  listByPaper: (paperId) => apiClient.get(`/evaluation/by-paper/${paperId}`),
}

export const questionBankAPI = {
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

  listReferenceMaterial: (syllabusId) =>
    apiClient.get('/reference-material', { params: { syllabus_id: syllabusId } }),

  uploadPaperTemplate: (syllabusId, files) => {
    const formData = new FormData()
    formData.append('syllabus_id', syllabusId)
    for (const file of files) {
      formData.append('files', file)
    }
    return apiClient.post('/upload-paper-template', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  getPaperTemplate: (syllabusId) =>
    apiClient.get('/paper-template', { params: { syllabus_id: syllabusId } }),

  updatePaperTemplate: (syllabusId, blueprint) =>
    apiClient.patch('/paper-template', { blueprint }, { params: { syllabus_id: syllabusId } }),

  generateQuestionBank: (syllabusId) =>
    apiClient.post('/generate-question-bank', { syllabus_id: syllabusId }),

  listQuestionBank: (syllabusId, params = {}) =>
    apiClient.get('/question-bank', {
      params: { syllabus_id: syllabusId, ...params },
    }),

  updateQuestion: (questionId, data) =>
    apiClient.patch(`/question-bank/${questionId}`, data),

  regenerateQuestion: (questionId) =>
    apiClient.post(`/question-bank/${questionId}/regenerate`),

  generateQuestionPaperFromTemplate: (syllabusId) =>
    apiClient.post('/generate-question-paper-from-template', { syllabus_id: syllabusId }),

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

  getFinalPaper: (paperId) =>
    apiClient.get('/final-paper', { params: { paper_id: paperId } }),

  updateFinalPaper: (paperId, data) =>
    apiClient.patch(`/final-paper/${paperId}`, data),

  updateFinalPaperQuestion: (paperId, questionNumber, data) =>
    apiClient.patch(`/final-paper/${paperId}/questions/${questionNumber}`, data),

  replaceFinalPaperQuestion: (paperId, questionNumber, slot = 'primary') =>
    apiClient.post(`/final-paper/${paperId}/questions/${questionNumber}/replace`, { slot }),

  finalizeFinalPaper: (paperId, status = 'finalized') =>
    apiClient.post(`/final-paper/${paperId}/finalize`, { status }),
}

export default apiClient
