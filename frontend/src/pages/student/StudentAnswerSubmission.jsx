import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { paperAPI, evaluationAPI } from '@/api/client'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Textarea from '@/components/ui/Textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Send } from 'lucide-react'

const StudentAnswerSubmission = () => {
  const { paperId } = useParams()
  const navigate = useNavigate()
  const [paper, setPaper] = useState(null)
  const [studentName, setStudentName] = useState('')
  const [answers, setAnswers] = useState({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadPaper()
  }, [paperId])

  const loadPaper = async () => {
    try {
      const response = await paperAPI.get(paperId)
      setPaper(response.data)
      // Initialize answer placeholders
      const answerMap = {}
      response.data.questions.forEach((q) => {
        answerMap[q.question_number] = ''
      })
      setAnswers(answerMap)
    } catch (error) {
      toast.error('Failed to load paper')
      navigate('/')
    } finally {
      setLoading(false)
    }
  }

  const handleAnswerChange = (questionNumber, text) => {
    setAnswers((prev) => ({
      ...prev,
      [questionNumber]: text,
    }))
  }

  const handleSubmit = async () => {
    if (!studentName.trim()) {
      toast.error('Please enter your name')
      return
    }

    if (Object.values(answers).every((a) => !a.trim())) {
      toast.error('Please answer at least one question')
      return
    }

    setSubmitting(true)
    try {
      // Convert answers to the expected format
      const answerItems = Object.entries(answers).map(([qNum, answerText]) => ({
        question_number: parseInt(qNum),
        answer_text: answerText,
      }))

      // Step 1: Submit raw answers
      const submissionResponse = await evaluationAPI.submitAnswers({
        paper_id: paperId,
        student_name: studentName,
        answers: answerItems,
      })

      const submissionId = submissionResponse.data.id

      // Step 2: Trigger evaluation for this submission
      const evaluationResponse = await evaluationAPI.evaluate({
        answer_id: submissionId,
      })

      const evaluationId = evaluationResponse.data.id

      toast.success('Answers submitted and evaluated!')

      // Navigate to evaluation results page using the evaluation ID
      setTimeout(() => {
        navigate(`/evaluation-results/${evaluationId}`)
      }, 800)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit or evaluate answers')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return <div className="text-center text-gray-500 py-8">Loading paper...</div>
  }

  if (!paper) {
    return <div className="text-center text-gray-500 py-8">Paper not found</div>
  }

  const renderSubQuestions = (items) => (
    <div className="ml-4 space-y-1 text-sm text-gray-700">
      {items.map((sub, idx) => (
        <p key={idx}>
          {sub.label ? <strong>{sub.label}) </strong> : null}
          {sub.text} ({sub.marks} marks)
        </p>
      ))}
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Submit Your Answers</h1>
        <p className="text-gray-600">{paper.exam_title}</p>
      </div>

      {/* Student Info */}
      <Card>
        <CardHeader>
          <CardTitle>Student Information</CardTitle>
        </CardHeader>
        <CardContent>
          <Input
            placeholder="Enter your name"
            value={studentName}
            onChange={(e) => setStudentName(e.target.value)}
          />
        </CardContent>
      </Card>

      {/* Exam Instructions */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <h4 className="font-semibold text-blue-900 mb-2">Exam Instructions:</h4>
          <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
            <li>Duration: {paper.duration_minutes} minutes</li>
            <li>Total Marks: {paper.total_marks}</li>
            <li>Answer all questions neatly</li>
            <li>Your answers will be evaluated using AI</li>
          </ul>
        </CardContent>
      </Card>

      {/* Question Answer Section */}
      <div className="space-y-6">
        {paper.questions.map((question) => (
          <div key={question.question_number} className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle>Question {question.question_number}</CardTitle>
                    <CardDescription>{question.topic}</CardDescription>
                  </div>
                  <span className="bg-gray-200 px-3 py-1 rounded text-sm font-semibold">
                    {question.marks} marks
                  </span>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Question Text */}
                <div>
                  <p className="text-gray-900 font-medium mb-2 whitespace-pre-line">{question.question_text}</p>

                  {/* Sub-questions */}
                  {question.sub_questions && question.sub_questions.length > 0 && renderSubQuestions(question.sub_questions)}

                  {(question.alternative_question_text || (question.alternative_sub_questions && question.alternative_sub_questions.length > 0)) && (
                    <div className="mt-4 rounded-md border border-gray-200 bg-gray-50 p-3">
                      <p className="mb-2 text-center text-sm font-semibold text-gray-600">(OR)</p>
                      {question.alternative_question_text ? (
                        <p className="text-gray-900 font-medium mb-2 whitespace-pre-line">{question.alternative_question_text}</p>
                      ) : null}
                      {question.alternative_sub_questions && question.alternative_sub_questions.length > 0 && renderSubQuestions(question.alternative_sub_questions)}
                    </div>
                  )}
                </div>

                {/* Answer Box */}
                <Textarea
                  placeholder="Write your answer here..."
                  value={answers[question.question_number] || ''}
                  onChange={(e) =>
                    handleAnswerChange(question.question_number, e.target.value)
                  }
                  rows={6}
                />
              </CardContent>
            </Card>

            {question.or_with_next && (
              <div className="text-center text-lg font-semibold text-gray-600">
                (OR)
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Submit Button */}
      <div className="flex gap-3">
        <Button onClick={handleSubmit} disabled={submitting} className="flex-1">
          <Send size={18} className="mr-2" />
          {submitting ? 'Submitting...' : 'Submit Answers'}
        </Button>
        <Button variant="outline" onClick={() => navigate('/')}>
          Cancel
        </Button>
      </div>
    </div>
  )
}

export default StudentAnswerSubmission
