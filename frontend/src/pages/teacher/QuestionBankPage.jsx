import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { syllabusAPI, questionBankAPI } from '@/api/client'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'

const REVIEW_STATUSES = ['pending', 'approved', 'edited', 'rejected']

const statusTone = {
  pending: 'secondary',
  approved: 'default',
  edited: 'secondary',
  rejected: 'destructive',
}

const QuestionBankPage = () => {
  const { syllabusId } = useParams()
  const navigate = useNavigate()
  const [syllabus, setSyllabus] = useState(null)
  const [bank, setBank] = useState([])
  const [loadingBank, setLoadingBank] = useState(false)
  const [uploadingRef, setUploadingRef] = useState(false)
  const [refFile, setRefFile] = useState(null)
  const [refDocs, setRefDocs] = useState([])
  const [statusFilter, setStatusFilter] = useState('all')
  const [unitFilter, setUnitFilter] = useState('all')
  const [bloomFilter, setBloomFilter] = useState('all')
  const [topicFilter, setTopicFilter] = useState('')
  const [editingId, setEditingId] = useState('')
  const [editingText, setEditingText] = useState('')
  const [busyQuestionId, setBusyQuestionId] = useState('')

  useEffect(() => {
    loadSyllabus()
    loadBank()
    loadReferenceMaterial()
  }, [syllabusId])

  const loadSyllabus = async () => {
    try {
      const response = await syllabusAPI.get(syllabusId)
      setSyllabus(response.data)
    } catch (error) {
      toast.error('Failed to load syllabus')
    }
  }

  const loadBank = async () => {
    setLoadingBank(true)
    try {
      const response = await questionBankAPI.listQuestionBank(syllabusId)
      setBank(response.data)
    } catch (error) {
      setBank([])
    } finally {
      setLoadingBank(false)
    }
  }

  const loadReferenceMaterial = async () => {
    try {
      const response = await questionBankAPI.listReferenceMaterial(syllabusId)
      setRefDocs(response.data || [])
    } catch {
      setRefDocs([])
    }
  }

  const handleUploadRef = async () => {
    if (!refFile) {
      toast.error('Please select a reference file')
      return
    }
    setUploadingRef(true)
    try {
      await questionBankAPI.uploadReferenceMaterial(syllabusId, refFile)
      toast.success('Reference material uploaded!')
      setRefFile(null)
      await loadReferenceMaterial()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upload reference material')
    } finally {
      setUploadingRef(false)
    }
  }

  const handleGenerateBank = async () => {
    setLoadingBank(true)
    try {
      const response = await questionBankAPI.generateQuestionBank(syllabusId)
      setBank(response.data)
      setEditingId('')
      setEditingText('')
      toast.success(`Generated ${response.data.length} questions in bank`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate question bank')
    } finally {
      setLoadingBank(false)
    }
  }

  const handleGeneratePaper = async () => {
    const curatedCount = bank.filter((q) => q.status === 'approved' || q.status === 'edited').length
    if (curatedCount === 0) {
      toast.error('Approve or edit some bank questions before generating a paper')
      return
    }

    try {
      const template = {
        syllabus_id: syllabusId,
        title: syllabus?.filename || 'Examination',
        sections: [
          { name: 'Section A', bloom_level: 'Remember', num_questions: 3 },
          { name: 'Section B', bloom_level: 'Apply', num_questions: 2 },
          { name: 'Section C', bloom_level: 'Analyze', num_questions: 1 },
        ],
      }
      const response = await questionBankAPI.generateQuestionPaper(template)
      toast.success('Question paper generated from curated question bank!')
      navigate(`/question-paper/${response.data.id}`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate question paper')
    }
  }

  const updateQuestionInState = (updatedQuestion) => {
    setBank((prev) => prev.map((question) => (question.id === updatedQuestion.id ? updatedQuestion : question)))
  }

  const handleStatusUpdate = async (questionId, status) => {
    setBusyQuestionId(questionId)
    try {
      const response = await questionBankAPI.updateQuestion(questionId, { status })
      updateQuestionInState(response.data)
      toast.success(`Question ${status}`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update question')
    } finally {
      setBusyQuestionId('')
    }
  }

  const handleSaveEdit = async (questionId) => {
    if (!editingText.trim()) {
      toast.error('Question text cannot be empty')
      return
    }

    setBusyQuestionId(questionId)
    try {
      const response = await questionBankAPI.updateQuestion(questionId, { question: editingText.trim() })
      updateQuestionInState(response.data)
      setEditingId('')
      setEditingText('')
      toast.success('Question updated')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update question')
    } finally {
      setBusyQuestionId('')
    }
  }

  const handleRegenerateQuestion = async (questionId) => {
    setBusyQuestionId(questionId)
    try {
      const response = await questionBankAPI.regenerateQuestion(questionId)
      updateQuestionInState(response.data)
      if (editingId === questionId) {
        setEditingId('')
        setEditingText('')
      }
      toast.success('Question regenerated')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to regenerate question')
    } finally {
      setBusyQuestionId('')
    }
  }

  const unitOptions = [...new Set(bank.map((q) => q.unit).filter(Boolean))]
  const filteredBank = bank.filter((question) => {
    if (statusFilter !== 'all' && question.status !== statusFilter) return false
    if (unitFilter !== 'all' && question.unit !== unitFilter) return false
    if (bloomFilter !== 'all' && question.bloom_level !== bloomFilter) return false
    if (topicFilter.trim() && !question.topic.toLowerCase().includes(topicFilter.trim().toLowerCase())) return false
    return true
  })

  const curatedCount = bank.filter((q) => q.status === 'approved' || q.status === 'edited').length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Question Bank Review</h1>
        <p className="text-gray-600">
          Curate the generated question bank first, then build the final paper from approved questions only.
        </p>
      </div>

      {syllabus && (
        <Card>
          <CardHeader>
            <CardTitle>{syllabus.filename}</CardTitle>
            <CardDescription>
              {syllabus.topics?.length || 0} units extracted | Uploaded{' '}
              {new Date(syllabus.created_at).toLocaleDateString()}
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Add More Reference Material (Optional)</CardTitle>
          <CardDescription>
            Upload more files if you want stronger grounding before regenerating or rebuilding the bank.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {refDocs.length > 0 && (
            <div className="text-sm text-gray-700">
              <p className="font-semibold mb-1">Already uploaded ({refDocs.length}):</p>
              <ul className="list-disc list-inside space-y-1">
                {refDocs.slice(0, 8).map((d) => (
                  <li key={d.id}>
                    {d.file_name}
                    {d.file_type ? ` (${d.file_type})` : ''}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <Input
            type="file"
            accept=".pdf,.docx,.doc,.txt"
            onChange={(e) => setRefFile(e.target.files?.[0] || null)}
          />
          <Button onClick={handleUploadRef} disabled={uploadingRef || !refFile}>
            {uploadingRef ? 'Uploading...' : 'Upload Reference Material'}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Generate Question Bank</CardTitle>
          <CardDescription>
            This generates the first draft. The next step is teacher review and curation.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button onClick={handleGenerateBank} disabled={loadingBank}>
            {loadingBank ? 'Generating question bank...' : 'Generate Question Bank'}
          </Button>

          {bank.length > 0 && (
            <div className="flex flex-wrap items-center justify-between gap-3 mt-2">
              <span className="text-sm text-gray-600">
                {bank.length} questions total | {curatedCount} curated for paper generation
              </span>
              <Button variant="outline" onClick={handleGeneratePaper}>
                Generate Question Paper from Curated Bank
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {bank.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Review Filters</CardTitle>
            <CardDescription>
              Filter questions by review state, unit, Bloom level, or topic before approving the final pool.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <select
              className="rounded-md border border-gray-300 px-3 py-2 text-sm"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All statuses</option>
              {REVIEW_STATUSES.map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
            <select
              className="rounded-md border border-gray-300 px-3 py-2 text-sm"
              value={unitFilter}
              onChange={(e) => setUnitFilter(e.target.value)}
            >
              <option value="all">All units</option>
              {unitOptions.map((unit) => (
                <option key={unit} value={unit}>{unit}</option>
              ))}
            </select>
            <select
              className="rounded-md border border-gray-300 px-3 py-2 text-sm"
              value={bloomFilter}
              onChange={(e) => setBloomFilter(e.target.value)}
            >
              <option value="all">All Bloom levels</option>
              <option value="Remember">Remember</option>
              <option value="Apply">Apply</option>
              <option value="Analyze">Analyze</option>
            </select>
            <Input
              placeholder="Filter by topic"
              value={topicFilter}
              onChange={(e) => setTopicFilter(e.target.value)}
            />
          </CardContent>
        </Card>
      )}

      {bank.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Bank Questions</CardTitle>
            <CardDescription>
              Approve, reject, edit, or regenerate questions before paper assembly.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 max-h-[640px] overflow-y-auto">
            {filteredBank.map((q) => {
              const isEditing = editingId === q.id
              const isBusy = busyQuestionId === q.id
              return (
                <div key={q.id} className="border rounded p-3 space-y-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge>{q.bloom_level}</Badge>
                    <Badge variant="secondary">{q.difficulty}</Badge>
                    <Badge variant={statusTone[q.status] || 'secondary'}>{q.status}</Badge>
                    {q.unit && (
                      <span className="ml-auto text-xs text-gray-500">Unit: {q.unit}</span>
                    )}
                  </div>

                  {isEditing ? (
                    <textarea
                      className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                      rows={4}
                      value={editingText}
                      onChange={(e) => setEditingText(e.target.value)}
                    />
                  ) : (
                    <p className="text-sm font-medium text-gray-900">{q.question}</p>
                  )}

                  <div className="text-xs text-gray-600 space-y-1">
                    {q.topic && <p>Topic: {q.topic}</p>}
                    <p>Question bank use: curated questions only go into the final paper.</p>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {isEditing ? (
                      <>
                        <Button size="sm" onClick={() => handleSaveEdit(q.id)} disabled={isBusy}>
                          {isBusy ? 'Saving...' : 'Save Edit'}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setEditingId('')
                            setEditingText('')
                          }}
                          disabled={isBusy}
                        >
                          Cancel
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button size="sm" onClick={() => handleStatusUpdate(q.id, 'approved')} disabled={isBusy}>
                          Approve
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => handleStatusUpdate(q.id, 'rejected')} disabled={isBusy}>
                          Reject
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setEditingId(q.id)
                            setEditingText(q.question)
                          }}
                          disabled={isBusy}
                        >
                          Edit
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => handleRegenerateQuestion(q.id)} disabled={isBusy}>
                          {isBusy ? 'Regenerating...' : 'Regenerate'}
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              )
            })}

            {filteredBank.length === 0 && (
              <div className="text-sm text-gray-500 py-8 text-center">
                No questions match the current filters.
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default QuestionBankPage
