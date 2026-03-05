import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { evaluationAPI } from '@/api/client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { Download, Home } from 'lucide-react'

const EvaluationResults = () => {
  const { evalId } = useParams()
  const navigate = useNavigate()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadResults()
  }, [evalId])

  const loadResults = async () => {
    try {
      const response = await evaluationAPI.getResults(evalId)
      setResult(response.data)
    } catch (error) {
      toast.error('Failed to load results')
      navigate('/')
    } finally {
      setLoading(false)
    }
  }

  const getGradeColor = (percentage) => {
    if (percentage >= 90) return 'bg-green-100 text-green-900 border-green-300'
    if (percentage >= 70) return 'bg-blue-100 text-blue-900 border-blue-300'
    if (percentage >= 50) return 'bg-yellow-100 text-yellow-900 border-yellow-300'
    return 'bg-red-100 text-red-900 border-red-300'
  }

  if (loading) {
    return <div className="text-center text-gray-500 py-8">Loading results...</div>
  }

  if (!result) {
    return <div className="text-center text-gray-500 py-8">Results not found</div>
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Evaluation Results</h1>
        <p className="text-gray-600">Student: {result.student_name}</p>
      </div>

      {/* Overall Score Card */}
      <Card className={`border-2 ${getGradeColor(result.percentage)}`}>
        <CardContent className="pt-6">
          <div className="text-center space-y-4">
            <div>
              <p className="text-sm font-medium mb-1">TOTAL SCORE</p>
              <p className="text-5xl font-bold">{result.total_marks}</p>
              <p className="text-lg text-gray-700">
                out of {result.max_marks} ({result.percentage}%)
              </p>
            </div>
            {result.overall_feedback && (
              <div className="text-sm font-medium">
                {result.overall_feedback}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Question-wise Breakdown */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Question Analysis</h2>
        <div className="space-y-4">
          {result.question_scores.map((score, idx) => {
            const percentage = (score.awarded_marks / score.max_marks) * 100
            return (
              <Card key={idx}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">
                        Question {score.question_number}
                      </CardTitle>
                      <CardDescription>
                        Score: {score.awarded_marks} / {score.max_marks} marks
                      </CardDescription>
                    </div>
                    <Badge
                      variant={percentage >= 70 ? 'success' : percentage >= 40 ? 'warning' : 'destructive'}
                    >
                      {Math.round(percentage)}%
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Scoring Metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div className="p-2 bg-gray-50 rounded">
                      <p className="text-xs text-gray-600 mb-1">Semantic Similarity</p>
                      <p className="text-lg font-bold text-gray-900">
                        {(score.semantic_similarity * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="p-2 bg-gray-50 rounded">
                      <p className="text-xs text-gray-600 mb-1">Completeness</p>
                      <p className="text-lg font-bold text-gray-900">
                        {(score.completeness * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="p-2 bg-gray-50 rounded">
                      <p className="text-xs text-gray-600 mb-1">Bloom Alignment</p>
                      <p className="text-lg font-bold text-gray-900">
                        {(score.bloom_alignment * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="p-2 bg-gray-50 rounded">
                      <p className="text-xs text-gray-600 mb-1">Logic & Reasoning</p>
                      <p className="text-lg font-bold text-gray-900">
                        {score.reasoning ? '✓' : '—'}
                      </p>
                    </div>
                  </div>

                  {/* Feedback */}
                  {score.feedback && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Feedback:</h4>
                      <p className="text-gray-700 text-sm bg-blue-50 p-3 rounded">
                        {score.feedback}
                      </p>
                    </div>
                  )}

                  {/* Scoring Rationale */}
                  {score.reasoning && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Scoring Rationale:</h4>
                      <p className="text-gray-700 text-sm bg-gray-50 p-3 rounded">
                        {score.reasoning}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <Button onClick={() => window.print()} variant="outline" className="flex-1">
          <Download size={18} className="mr-2" />
          Download Results
        </Button>
        <Button onClick={() => navigate('/dashboard')} className="flex-1">
          <Home size={18} className="mr-2" />
          Go to Home
        </Button>
      </div>
    </div>
  )
}

export default EvaluationResults
