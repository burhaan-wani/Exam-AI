import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { questionBankAPI } from '@/api/client'
import Button from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import { Download, Share2, Printer, RefreshCw } from 'lucide-react'
import html2pdf from 'html2pdf.js'

const QuestionPaperView = () => {
  const { paperId } = useParams()
  const navigate = useNavigate()
  const [paper, setPaper] = useState(null)
  const [loading, setLoading] = useState(true)
  const [reviewingQuestion, setReviewingQuestion] = useState(null)

  useEffect(() => {
    loadPaper()
  }, [paperId])

  const loadPaper = async () => {
    try {
      const response = await questionBankAPI.getFinalPaper(paperId)
      setPaper(response.data)
    } catch (error) {
      toast.error('Failed to load paper')
      navigate('/dashboard')
    } finally {
      setLoading(false)
    }
  }

  const handlePrint = () => {
    window.print()
  }

  const handleDownloadPDF = async () => {
    if (!paper) return

    try {
      const element = document.getElementById('question-paper')

      if (!element) {
        toast.error('Could not find paper content to export')
        return
      }

      const options = {
        margin: 0.5,
        filename: `${paper.exam_title || 'question-paper'}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' },
      }

      await html2pdf().from(element).set(options).save()
    } catch (error) {
      console.error(error)
      toast.error('Failed to generate PDF')
    }
  }

  const handleSharePaper = () => {
    const url = `${window.location.origin}/submit-answers/${paperId}`
    navigator.clipboard.writeText(url)
    toast.success('Link copied to clipboard!')
  }

  const handleReplaceQuestion = async (questionNumber) => {
    setReviewingQuestion(questionNumber)
    try {
      await questionBankAPI.reviewQuestionInPaper(paperId, questionNumber)
      await loadPaper()
      toast.success(`Question ${questionNumber} replaced`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Could not replace question')
    } finally {
      setReviewingQuestion(null)
    }
  }

  if (loading) {
    return <div className="text-center text-gray-500 py-8">Loading paper...</div>
  }

  if (!paper) {
    return <div className="text-center text-gray-500 py-8">Paper not found</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-3 no-print">
        <Button onClick={handlePrint}>
          <Printer size={18} className="mr-2" />
          Print
        </Button>
        <Button onClick={handleDownloadPDF} variant="outline">
          <Download size={18} className="mr-2" />
          Download PDF
        </Button>
        <Button onClick={handleSharePaper} variant="outline">
          <Share2 size={18} className="mr-2" />
          Share with Students
        </Button>
      </div>

      <Card className="no-print border-blue-200 bg-blue-50">
        <CardContent className="pt-6 text-sm text-blue-900">
          This view is the final teacher review step in the new pipeline. If a question is not a good fit, replace it here and the paper will be refreshed from the question bank.
        </CardContent>
      </Card>

      <div
        id="question-paper"
        className="max-w-4xl mx-auto bg-white p-12 shadow-lg print:shadow-none print:p-0 print:max-w-full"
      >
        <div className="text-center mb-8 border-b pb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{paper.exam_title}</h1>
          <div className="text-sm text-gray-700 space-y-1">
            <p>Duration: {paper.duration_minutes} minutes</p>
            <p>Total Marks: {paper.total_marks}</p>
          </div>
        </div>

        <div className="mb-8 p-4 bg-gray-50 rounded text-sm text-gray-700">
          <h3 className="font-semibold text-gray-900 mb-2">Instructions:</h3>
          <ul className="list-disc list-inside space-y-1 text-xs">
            <li>Answer all questions</li>
            <li>Write clearly and legibly</li>
            <li>Marks are indicated for each question</li>
            <li>Use separate sheets if needed</li>
          </ul>
        </div>

        <div className="space-y-6">
          {paper.questions.map((question) => (
            <div key={question.question_number} className="mb-6">
              <div className="flex justify-between items-start gap-4 mb-2">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">
                    Question {question.question_number}
                  </h3>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500 print:hidden">
                    {question.topic && <span>Topic: {question.topic}</span>}
                    {question.unit && <span>Unit: {question.unit}</span>}
                    {question.bloom_level && <span>Bloom: {question.bloom_level}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="bg-gray-200 px-3 py-1 rounded text-sm font-semibold text-gray-900">
                    {question.marks} marks
                  </span>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="print:hidden"
                    disabled={reviewingQuestion === question.question_number}
                    onClick={() => handleReplaceQuestion(question.question_number)}
                  >
                    <RefreshCw size={14} className="mr-2" />
                    {reviewingQuestion === question.question_number ? 'Replacing...' : 'Replace'}
                  </Button>
                </div>
              </div>

              <p className="text-gray-800 mb-3 leading-relaxed">{question.question_text}</p>

              {question.sub_questions && question.sub_questions.length > 0 && (
                <div className="ml-6 space-y-2 mb-4">
                  {question.sub_questions.map((sub, idx) => (
                    <div key={idx}>
                      <p className="text-gray-800">
                        <span className="font-semibold">{sub.label}</span>{' '}
                        ({sub.marks} marks): {sub.text}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              <div className="ml-6 border-l-2 border-gray-300 pl-4 py-8 text-gray-400 text-sm">
                [Answer space for student]
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 pt-6 border-t text-center text-xs text-gray-600">
          <p>End of Question Paper</p>
          <p className="mt-2 text-gray-500">
            Generated by Exam AI {paper.created_at ? `- ${new Date(paper.created_at).toLocaleDateString()}` : ''}
          </p>
        </div>
      </div>
    </div>
  )
}

export default QuestionPaperView
