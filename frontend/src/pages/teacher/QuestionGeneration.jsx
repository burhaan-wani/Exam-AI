import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { questionsAPI } from '@/api/client'
import Button from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import { CheckCircle, XCircle, Loader } from 'lucide-react'

const QuestionGeneration = () => {
  const { blueprintId } = useParams()
  const navigate = useNavigate()
  const [blueprint, setBlueprint] = useState(null)
  const [questions, setQuestions] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    loadBlueprint()
  }, [blueprintId])

  const loadBlueprint = async () => {
    try {
      const response = await questionsAPI.getBlueprint(blueprintId)
      setBlueprint(response.data)
    } catch (error) {
      toast.error('Failed to load blueprint')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      const response = await questionsAPI.generate({
        blueprint_id: blueprintId,
      })

      setQuestions(response.data.questions)
      toast.success(`Generated ${response.data.count} questions!`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate questions')
    } finally {
      setGenerating(false)
    }
  }

  const handleReview = () => {
    navigate(`/review-questions/${blueprintId}`)
  }

  if (loading) {
    return <div className="text-center text-gray-500 py-8">Loading...</div>
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Generate Questions</h1>
        <p className="text-gray-600">
          AI will generate questions based on your Bloom configuration
        </p>
      </div>

      {/* Blueprint Info */}
      {blueprint && (
        <Card>
          <CardHeader>
            <CardTitle>{blueprint.exam_title}</CardTitle>
            <CardDescription>
              Duration: {blueprint.duration_minutes} mins • Total Marks: {blueprint.total_marks}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <h4 className="font-semibold text-gray-900">Configurations:</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {blueprint.configs.map((config, idx) => (
                  <div key={idx} className="text-sm p-2 bg-gray-50 rounded">
                    <p className="font-medium">{config.topic}</p>
                    <p className="text-gray-600">
                      {config.num_questions} questions × {config.marks_per_question} marks • {config.bloom_level} • {config.difficulty}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Generation Button */}
      {questions.length === 0 ? (
        <Card className="text-center p-8">
          <Loader className="w-12 h-12 text-gray-400 mx-auto mb-4 animate-spin" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Ready to Generate?</h3>
          <p className="text-gray-600 mb-6">
            Click below to generate AI-powered questions based on your configuration.
          </p>
          <Button onClick={handleGenerate} disabled={generating} size="lg">
            {generating ? 'Generating questions...' : 'Generate Questions'}
          </Button>
        </Card>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Generated Questions</h2>
              <p className="text-gray-600">{questions.length} questions created</p>
            </div>
            <Badge variant="success">Ready</Badge>
          </div>

          {/* Questions List */}
          <div className="space-y-3">
            {questions.map((question, idx) => (
              <Card key={idx}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge>{question.bloom_level}</Badge>
                        <Badge variant="secondary">{question.difficulty}</Badge>
                        <span className="text-sm text-gray-600">{question.marks} marks</span>
                      </div>
                      <p className="text-gray-900 font-medium mb-2">{question.question_text}</p>
                      {question.sub_questions?.length > 0 && (
                        <div className="ml-4 space-y-1 text-sm text-gray-700">
                          {question.sub_questions.map((sub, sidx) => (
                            <p key={sidx}>
                              <strong>{sub.label}</strong> ({sub.marks} marks): {sub.text}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-1" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <Button onClick={handleReview} className="flex-1">
              Review & Refine Questions
            </Button>
            <Button variant="outline" onClick={() => navigate('/dashboard')}>
              Go to Dashboard
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

export default QuestionGeneration
