import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import html2pdf from 'html2pdf.js'
import { Download, Pencil, RefreshCw, Save, Share2 } from 'lucide-react'
import { toast } from 'sonner'
import { questionBankAPI } from '@/api/client'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import Textarea from '@/components/ui/Textarea'

const cloneValue = (value) => JSON.parse(JSON.stringify(value))

const emptySubQuestion = () => ({
  label: '',
  text: '',
  marks: 0,
  model_answer: '',
  bank_id: '',
})

const normalizeQuestionForEdit = (question) => ({
  question_text: question.question_text || '',
  sub_questions: cloneValue(question.sub_questions || []),
  alternative_question_text: question.alternative_question_text || '',
  alternative_sub_questions: cloneValue(question.alternative_sub_questions || []),
  marks: question.marks || 0,
  bloom_level: question.bloom_level || '',
  topic: question.topic || '',
  unit: question.unit || '',
  or_with_next: !!question.or_with_next,
})

const QuestionPaperView = () => {
  const { paperId } = useParams()
  const navigate = useNavigate()
  const [paper, setPaper] = useState(null)
  const [loading, setLoading] = useState(true)
  const [savingMeta, setSavingMeta] = useState(false)
  const [busyAction, setBusyAction] = useState('')
  const [editingQuestion, setEditingQuestion] = useState(null)
  const [questionDraft, setQuestionDraft] = useState(null)
  const [paperMeta, setPaperMeta] = useState({
    exam_title: '',
    total_marks: 0,
    duration_minutes: 180,
  })

  useEffect(() => {
    loadPaper()
  }, [paperId])

  const loadPaper = async () => {
    try {
      const response = await questionBankAPI.getFinalPaper(paperId)
      setPaper(response.data)
      setPaperMeta({
        exam_title: response.data.exam_title || '',
        total_marks: response.data.total_marks || 0,
        duration_minutes: response.data.duration_minutes || 180,
      })
    } catch (error) {
      toast.error('Failed to load paper')
      navigate('/dashboard')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadPDF = async () => {
    if (!paper) return
    const element = document.getElementById('question-paper')
    if (!element) {
      toast.error('Could not find paper content to export')
      return
    }

    try {
      await html2pdf()
        .from(element)
        .set({
          margin: 0.5,
          filename: `${paper.exam_title || 'question-paper'}.pdf`,
          image: { type: 'jpeg', quality: 0.98 },
          html2canvas: { scale: 2 },
          jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' },
        })
        .save()
    } catch (error) {
      console.error(error)
      toast.error('Failed to generate PDF')
    }
  }

  const handleSharePaper = async () => {
    if (paper?.status !== 'finalized') {
      toast.error('Finalize the paper before sharing it with students')
      return
    }

    const url = `${window.location.origin}/submit-answers/${paperId}`
    await navigator.clipboard.writeText(url)
    toast.success('Student paper link copied to clipboard')
  }

  const handleSaveMeta = async () => {
    setSavingMeta(true)
    try {
      const response = await questionBankAPI.updateFinalPaper(paperId, paperMeta)
      setPaper(response.data)
      setPaperMeta({
        exam_title: response.data.exam_title || '',
        total_marks: response.data.total_marks || 0,
        duration_minutes: response.data.duration_minutes || 180,
      })
      toast.success('Paper details updated')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update paper details')
    } finally {
      setSavingMeta(false)
    }
  }

  const startEditingQuestion = (question) => {
    setEditingQuestion(question.question_number)
    setQuestionDraft(normalizeQuestionForEdit(question))
  }

  const stopEditingQuestion = () => {
    setEditingQuestion(null)
    setQuestionDraft(null)
  }

  const updateDraft = (field, value) => {
    setQuestionDraft((prev) => ({ ...prev, [field]: value }))
  }

  const updateSubQuestion = (field, value, index, slot) => {
    setQuestionDraft((prev) => {
      const next = cloneValue(prev)
      next[slot][index][field] = field === 'label' || field === 'text' ? value : Number(value) || 0
      return next
    })
  }

  const addSubQuestion = (slot) => {
    setQuestionDraft((prev) => {
      const next = cloneValue(prev)
      next[slot].push(emptySubQuestion())
      if (slot === 'sub_questions') next.question_text = ''
      if (slot === 'alternative_sub_questions') next.alternative_question_text = ''
      return next
    })
  }

  const removeSubQuestion = (slot, index) => {
    setQuestionDraft((prev) => {
      const next = cloneValue(prev)
      next[slot].splice(index, 1)
      return next
    })
  }

  const handleSaveQuestion = async (questionNumber) => {
    setBusyAction(`save-${questionNumber}`)
    try {
      const payload = {
        ...questionDraft,
        marks: Number(questionDraft.marks) || 0,
      }
      const response = await questionBankAPI.updateFinalPaperQuestion(paperId, questionNumber, payload)
      setPaper(response.data)
      stopEditingQuestion()
      toast.success(`Question ${questionNumber} updated`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update question')
    } finally {
      setBusyAction('')
    }
  }

  const handleReplaceQuestion = async (questionNumber, slot = 'primary') => {
    setBusyAction(`replace-${questionNumber}-${slot}`)
    try {
      const response = await questionBankAPI.replaceFinalPaperQuestion(paperId, questionNumber, slot)
      setPaper(response.data)
      if (editingQuestion === questionNumber) {
        const updatedQuestion = response.data.questions.find((question) => question.question_number === questionNumber)
        if (updatedQuestion) {
          setQuestionDraft(normalizeQuestionForEdit(updatedQuestion))
        }
      }
      toast.success(slot === 'alternative' ? `Alternative for Q${questionNumber} replaced` : `Question ${questionNumber} replaced`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Could not replace question')
    } finally {
      setBusyAction('')
    }
  }

  const handleFinalize = async (status) => {
    setBusyAction(status)
    try {
      const response = await questionBankAPI.finalizeFinalPaper(paperId, status)
      setPaper(response.data)
      toast.success(status === 'finalized' ? 'Paper finalized and ready for students' : 'Paper moved back to draft')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update paper status')
    } finally {
      setBusyAction('')
    }
  }

  const renderSubQuestions = (items) => (
    <div className="ml-6 space-y-2">
      {items.map((sub, idx) => (
        <p key={`${sub.label}-${idx}`} className="text-gray-800">
          {sub.label ? <span className="font-semibold">{sub.label}) </span> : null}
          {sub.text}
          <span className="text-sm text-gray-500"> ({sub.marks} marks)</span>
        </p>
      ))}
    </div>
  )

  if (loading) {
    return <div className="py-8 text-center text-gray-500">Loading paper...</div>
  }

  if (!paper) {
    return <div className="py-8 text-center text-gray-500">Paper not found</div>
  }

  const isFinalized = paper.status === 'finalized'

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-3 no-print" data-html2canvas-ignore="true">
        <Button onClick={handleDownloadPDF} variant="outline">
          <Download size={18} className="mr-2" />
          Download PDF
        </Button>
        <Button onClick={handleSharePaper} variant="outline" disabled={!isFinalized}>
          <Share2 size={18} className="mr-2" />
          Copy Student Link
        </Button>
        {isFinalized ? (
          <Button variant="outline" onClick={() => handleFinalize('draft')} disabled={busyAction === 'draft'}>
            {busyAction === 'draft' ? 'Updating...' : 'Move Back to Draft'}
          </Button>
        ) : (
          <Button onClick={() => handleFinalize('finalized')} disabled={busyAction === 'finalized'}>
            {busyAction === 'finalized' ? 'Finalizing...' : 'Approve Final Paper'}
          </Button>
        )}
      </div>

      <Card
        className={isFinalized ? 'border-green-200 bg-green-50' : 'border-amber-200 bg-amber-50'}
        data-html2canvas-ignore="true"
      >
        <CardContent className="space-y-3 pt-6 text-sm">
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-semibold text-gray-900">Final-Paper HITL</span>
            <Badge variant={isFinalized ? 'default' : 'secondary'}>{paper.status}</Badge>
            {paper.finalized_at ? <span className="text-gray-600">Published {new Date(paper.finalized_at).toLocaleString()}</span> : null}
          </div>
          <p className="text-gray-700">
            {isFinalized
              ? 'This paper is approved. You can copy the student link to share it, or move it back to draft if you need more edits.'
              : 'This paper is still in teacher review. Edit wording, subparts, marks, OR behavior, or replace questions before approving the final paper.'}
          </p>
          <div className="rounded border border-white/70 bg-white/70 p-3 text-xs text-gray-700">
            <p>
              <span className="font-semibold text-gray-900">Approve Final Paper:</span> locks this draft in as the official paper version.
            </p>
            <p className="mt-1">
              <span className="font-semibold text-gray-900">Copy Student Link:</span> copies the student-facing access link after the paper has been approved.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card className="no-print" data-html2canvas-ignore="true">
        <CardContent className="space-y-3 pt-6">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <Input
              value={paperMeta.exam_title}
              onChange={(e) => setPaperMeta((prev) => ({ ...prev, exam_title: e.target.value }))}
              placeholder="Exam title"
            />
            <Input
              type="number"
              value={paperMeta.total_marks}
              onChange={(e) => setPaperMeta((prev) => ({ ...prev, total_marks: Number(e.target.value) || 0 }))}
              placeholder="Total marks"
            />
            <Input
              type="number"
              value={paperMeta.duration_minutes}
              onChange={(e) => setPaperMeta((prev) => ({ ...prev, duration_minutes: Number(e.target.value) || 0 }))}
              placeholder="Duration in minutes"
            />
          </div>
          <Button onClick={handleSaveMeta} disabled={savingMeta}>
            <Save size={16} className="mr-2" />
            {savingMeta ? 'Saving...' : 'Save Paper Details'}
          </Button>
        </CardContent>
      </Card>

      <div
        id="question-paper"
        className="mx-auto max-w-4xl bg-white p-12 shadow-lg print:max-w-full print:p-0 print:shadow-none"
      >
        <div className="mb-8 border-b pb-6 text-center">
          <h1 className="mb-2 text-3xl font-bold text-gray-900">{paper.exam_title}</h1>
          <div className="space-y-1 text-sm text-gray-700">
            <p>Duration: {paper.duration_minutes} minutes</p>
            <p>Total Marks: {paper.total_marks}</p>
          </div>
        </div>

        <div className="mb-8 rounded bg-gray-50 p-4 text-sm text-gray-700">
          <h3 className="mb-2 font-semibold text-gray-900">Instructions:</h3>
          <ul className="list-inside list-disc space-y-1 text-xs">
            <li>Answer all questions</li>
            <li>Write clearly and legibly</li>
            <li>Marks are indicated for each question</li>
            <li>Use separate sheets if needed</li>
          </ul>
        </div>

        <div className="space-y-8">
          {paper.questions.map((question) => {
            const isEditing = editingQuestion === question.question_number
            const hasAlternative = !!(
              question.alternative_question_text ||
              (question.alternative_sub_questions && question.alternative_sub_questions.length > 0)
            )

            return (
              <div key={question.question_number} className="space-y-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">Question {question.question_number}</h3>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500 print:hidden">
                      {question.topic ? <span>Topic: {question.topic}</span> : null}
                      {question.unit ? <span>Unit: {question.unit}</span> : null}
                      {question.bloom_level ? <span>Bloom: {question.bloom_level}</span> : null}
                    </div>
                  </div>
                  <span className="rounded bg-gray-200 px-3 py-1 text-sm font-semibold text-gray-900">
                    {question.marks} marks
                  </span>
                </div>

                {isEditing ? (
                  <div
                    className="space-y-4 rounded border border-gray-200 bg-gray-50 p-4 print:hidden"
                    data-html2canvas-ignore="true"
                  >
                    <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
                      <Input value={questionDraft.unit} onChange={(e) => updateDraft('unit', e.target.value)} placeholder="Unit" />
                      <Input value={questionDraft.topic} onChange={(e) => updateDraft('topic', e.target.value)} placeholder="Topic" />
                      <Input value={questionDraft.bloom_level} onChange={(e) => updateDraft('bloom_level', e.target.value)} placeholder="Bloom level" />
                      <Input type="number" value={questionDraft.marks} onChange={(e) => updateDraft('marks', Number(e.target.value) || 0)} placeholder="Marks" />
                    </div>

                    <div className="space-y-2">
                      <p className="font-medium text-gray-900">Primary slot</p>
                      <Textarea
                        rows={3}
                        value={questionDraft.question_text}
                        onChange={(e) => updateDraft('question_text', e.target.value)}
                        placeholder="Primary question text"
                      />
                      <div className="space-y-2">
                        {questionDraft.sub_questions.map((sub, index) => (
                          <div key={index} className="grid grid-cols-1 gap-2 md:grid-cols-5">
                            <Input value={sub.label} onChange={(e) => updateSubQuestion('label', e.target.value, index, 'sub_questions')} placeholder="Label" />
                            <Input type="number" value={sub.marks} onChange={(e) => updateSubQuestion('marks', e.target.value, index, 'sub_questions')} placeholder="Marks" />
                            <div className="md:col-span-2">
                              <Input value={sub.text} onChange={(e) => updateSubQuestion('text', e.target.value, index, 'sub_questions')} placeholder="Subpart text" />
                            </div>
                            <Button size="sm" variant="outline" onClick={() => removeSubQuestion('sub_questions', index)}>
                              Remove
                            </Button>
                          </div>
                        ))}
                        <div className="flex flex-wrap gap-2">
                          <Button size="sm" variant="outline" onClick={() => addSubQuestion('sub_questions')}>Add Primary Subpart</Button>
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={busyAction === `replace-${question.question_number}-primary`}
                            onClick={() => handleReplaceQuestion(question.question_number, 'primary')}
                          >
                            <RefreshCw size={14} className="mr-2" />
                            Replace Primary
                          </Button>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-medium text-gray-900">Internal OR slot</p>
                        <label className="flex items-center gap-2 text-sm text-gray-700">
                          <input
                            type="checkbox"
                            checked={questionDraft.or_with_next}
                            onChange={(e) => updateDraft('or_with_next', e.target.checked)}
                          />
                          OR with next question
                        </label>
                      </div>
                      <Textarea
                        rows={3}
                        value={questionDraft.alternative_question_text}
                        onChange={(e) => updateDraft('alternative_question_text', e.target.value)}
                        placeholder="Alternative question text (optional)"
                      />
                      <div className="space-y-2">
                        {questionDraft.alternative_sub_questions.map((sub, index) => (
                          <div key={index} className="grid grid-cols-1 gap-2 md:grid-cols-5">
                            <Input value={sub.label} onChange={(e) => updateSubQuestion('label', e.target.value, index, 'alternative_sub_questions')} placeholder="Label" />
                            <Input type="number" value={sub.marks} onChange={(e) => updateSubQuestion('marks', e.target.value, index, 'alternative_sub_questions')} placeholder="Marks" />
                            <div className="md:col-span-2">
                              <Input value={sub.text} onChange={(e) => updateSubQuestion('text', e.target.value, index, 'alternative_sub_questions')} placeholder="Alternative subpart text" />
                            </div>
                            <Button size="sm" variant="outline" onClick={() => removeSubQuestion('alternative_sub_questions', index)}>
                              Remove
                            </Button>
                          </div>
                        ))}
                        <div className="flex flex-wrap gap-2">
                          <Button size="sm" variant="outline" onClick={() => addSubQuestion('alternative_sub_questions')}>Add OR Subpart</Button>
                          {hasAlternative || questionDraft.alternative_sub_questions.length > 0 || questionDraft.alternative_question_text ? (
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={busyAction === `replace-${question.question_number}-alternative`}
                              onClick={() => handleReplaceQuestion(question.question_number, 'alternative')}
                            >
                              <RefreshCw size={14} className="mr-2" />
                              Replace OR Slot
                            </Button>
                          ) : null}
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <Button onClick={() => handleSaveQuestion(question.question_number)} disabled={busyAction === `save-${question.question_number}`}>
                        <Save size={14} className="mr-2" />
                        {busyAction === `save-${question.question_number}` ? 'Saving...' : 'Save Question'}
                      </Button>
                      <Button variant="outline" onClick={stopEditingQuestion}>Cancel</Button>
                    </div>
                  </div>
                ) : (
                  <>
                    {question.question_text ? <p className="whitespace-pre-line text-gray-800">{question.question_text}</p> : null}
                    {question.sub_questions?.length > 0 ? renderSubQuestions(question.sub_questions) : null}

                    {hasAlternative ? (
                      <div className="space-y-3 rounded border border-gray-200 bg-gray-50 p-4">
                        <p className="text-center text-sm font-semibold text-gray-700">(OR)</p>
                        {question.alternative_question_text ? <p className="whitespace-pre-line text-gray-800">{question.alternative_question_text}</p> : null}
                        {question.alternative_sub_questions?.length > 0 ? renderSubQuestions(question.alternative_sub_questions) : null}
                      </div>
                    ) : null}

                    {question.or_with_next ? (
                      <div className="my-4 text-center text-lg font-semibold text-gray-700">(OR)</div>
                    ) : null}

                    <div className="flex flex-wrap gap-2 print:hidden" data-html2canvas-ignore="true">
                      <Button size="sm" variant="outline" onClick={() => startEditingQuestion(question)}>
                        <Pencil size={14} className="mr-2" />
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={busyAction === `replace-${question.question_number}-primary`}
                        onClick={() => handleReplaceQuestion(question.question_number, 'primary')}
                      >
                        <RefreshCw size={14} className="mr-2" />
                        Replace
                      </Button>
                    </div>
                  </>
                )}
              </div>
            )
          })}
        </div>

        <div className="mt-12 border-t pt-6 text-center text-xs text-gray-600">
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
