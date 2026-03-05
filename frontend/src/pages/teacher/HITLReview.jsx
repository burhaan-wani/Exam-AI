import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { questionsAPI, hitlAPI, paperAPI } from '@/api/client'
import Button from '@/components/ui/Button'
import Textarea from '@/components/ui/Textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import { CheckCircle, XCircle, AlertCircle, RefreshCw } from 'lucide-react'

const HITLReview = () => {
  const { blueprintId } = useParams()
  const navigate = useNavigate()
  const [questions, setQuestions] = useState([])
  const [loading, setLoading] = useState(true)
  const [reviewingIdx, setReviewingIdx] = useState(null)
  const [feedback, setFeedback] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadQuestions()
  }, [blueprintId])

  const loadQuestions = async () => {
    try {
      const response = await questionsAPI.listByBlueprint(blueprintId)
      setQuestions(response.data)
    } catch (error) {
      toast.error('Failed to load questions')
    } finally {
      setLoading(false)
    }
  }

  const handleReview = async (questionId, action, feedbackText = '') => {
    setSubmitting(true)
    try {
      await hitlAPI.review({
        question_id: questionId,
        action,
        feedback_note: feedbackText || null,
        modified_text: null,
      })

      toast.success(`Question ${action}!`)
      setReviewingIdx(null)
      setFeedback('')
      await loadQuestions()
    } catch (error) {
      toast.error('Action failed')
    } finally {
      setSubmitting(false)
    }
  }

  const handleAssemble = async () => {
    try {
      const response = await paperAPI.assemble({ blueprint_id: blueprintId })
      toast.success('Question paper assembled!')
      navigate(`/question-paper/${response.data.id}`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to assemble paper')
    }
  }

  if (loading) {
    return <div className="text-center text-gray-500 py-8">Loading...</div>
  }

  const approved = questions.filter((q) => q.status === 'approved').length
  const total = questions.length

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Review Questions (HITL)</h1>
        <p className="text-gray-600">
          Review generated questions, approve them, or request changes
        </p>
      </div>

      {/* Progress */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Progress</span>
            <span className="text-sm font-bold text-gray-900">
              {approved}/{total} approved
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-green-600 h-2 rounded-full transition-all"
              style={{ width: `${(approved / total) * 100}%` }}
            ></div>
          </div>
        </CardContent>
      </Card>

      {/* Questions */}
      <div className="space-y-3">
        {questions.map((question, idx) => (
          <Card key={question.id} className={question.status === 'approved' ? 'border-green-200' : ''}>
            <CardContent className="p-4">
              <div className="space-y-3">
                {/* Question Header */}
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-bold text-gray-900">Q{idx + 1}</span>
                      <Badge>{question.bloom_level}</Badge>
                      <Badge variant="secondary">{question.difficulty}</Badge>
                      <span className="text-sm text-gray-600 ml-auto">{question.marks} marks</span>
                    </div>
                    <p className="text-gray-900 font-medium mb-2">{question.question_text}</p>

                    {/* Sub-questions */}
                    {question.sub_questions?.length > 0 && (
                      <div className="ml-4 space-y-1 text-sm text-gray-700 mb-3">
                        {question.sub_questions.map((sub, sidx) => (
                          <p key={sidx}>
                            <strong>{sub.label}</strong> ({sub.marks}): {sub.text}
                          </p>
                        ))}
                      </div>
                    )}

                    {/* Model Answer */}
                    {question.model_answer && (
                      <div className="mt-2 p-2 bg-gray-50 rounded text-sm">
                        <p className="font-semibold text-gray-700 mb-1">Model Answer:</p>
                        <p className="text-gray-600">{question.model_answer.substring(0, 200)}...</p>
                      </div>
                    )}
                  </div>

                  {/* Status Badge */}
                  <div>
                    {question.status === 'approved' && (
                      <CheckCircle className="w-6 h-6 text-green-600" />
                    )}
                    {question.status === 'rejected' && (
                      <XCircle className="w-6 h-6 text-red-600" />
                    )}
                    {question.status === 'pending' && (
                      <AlertCircle className="w-6 h-6 text-yellow-600" />
                    )}
                  </div>
                </div>

                {/* Actions */}
                {question.status === 'pending' && (
                  <div className="border-t pt-3 space-y-2">
                    {reviewingIdx === idx ? (
                      <div className="space-y-2">
                        <Textarea
                          placeholder="Enter feedback for regeneration..."
                          value={feedback}
                          onChange={(e) => setFeedback(e.target.value)}
                          rows={3}
                        />
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() =>
                              handleReview(question.id, 'regenerate', feedback)
                            }
                            disabled={!feedback || submitting}
                          >
                            Regenerate
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setReviewingIdx(null)
                              setFeedback('')
                            }}
                            disabled={submitting}
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          onClick={() =>
                            handleReview(question.id, 'approved')
                          }
                          disabled={submitting}
                          className="flex-1"
                        >
                          <CheckCircle size={16} className="mr-2" />
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setReviewingIdx(idx)
                            setFeedback('')
                          }}
                          disabled={submitting}
                          className="flex-1"
                        >
                          <RefreshCw size={16} className="mr-2" />
                          Request Changes
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() =>
                            handleReview(question.id, 'rejected')
                          }
                          disabled={submitting}
                          className="flex-1"
                        >
                          <XCircle size={16} className="mr-2" />
                          Reject
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Assemble Button */}
      {approved === total && total > 0 && (
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-6">
            <p className="text-green-900 mb-4">
              All questions approved! Ready to assemble the final question paper.
            </p>
            <Button onClick={handleAssemble} className="w-full">
              Assemble Question Paper
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default HITLReview
