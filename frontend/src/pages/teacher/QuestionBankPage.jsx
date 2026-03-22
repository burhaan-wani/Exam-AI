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

const formatSubpartMarks = (subparts = []) =>
  subparts
    .map((subpart) => `${subpart.label || 'full'}:${subpart.marks || 0}`)
    .join(', ')

const cloneBlueprint = (blueprint) => JSON.parse(JSON.stringify(blueprint || {}))

const QuestionBankPage = () => {
  const { syllabusId } = useParams()
  const navigate = useNavigate()
  const [syllabus, setSyllabus] = useState(null)
  const [bank, setBank] = useState([])
  const [loadingBank, setLoadingBank] = useState(false)
  const [uploadingRef, setUploadingRef] = useState(false)
  const [refFile, setRefFile] = useState(null)
  const [refDocs, setRefDocs] = useState([])
  const [templateFiles, setTemplateFiles] = useState([])
  const [templateDoc, setTemplateDoc] = useState(null)
  const [uploadingTemplate, setUploadingTemplate] = useState(false)
  const [savingTemplate, setSavingTemplate] = useState(false)
  const [editableBlueprint, setEditableBlueprint] = useState(null)
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
    loadPaperTemplate()
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

  const loadPaperTemplate = async () => {
    try {
      const response = await questionBankAPI.getPaperTemplate(syllabusId)
      setTemplateDoc(response.data)
      setEditableBlueprint(cloneBlueprint(response.data.blueprint))
    } catch {
      setTemplateDoc(null)
      setEditableBlueprint(null)
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
    if (!templateDoc) {
      toast.error('Upload a previous paper template before generating the final paper')
      return
    }
    if (!templateDoc.validation?.is_valid) {
      toast.error('Review and fix the blueprint issues before generating the final paper')
      return
    }

    try {
      const response = await questionBankAPI.generateQuestionPaperFromTemplate(syllabusId)
      toast.success('Question paper generated from curated bank and uploaded template!')
      navigate(`/question-paper/${response.data.id}`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate question paper')
    }
  }

  const handleUploadTemplate = async () => {
    if (templateFiles.length === 0) {
      toast.error('Please select one or more template files')
      return
    }

    setUploadingTemplate(true)
    try {
      const response = await questionBankAPI.uploadPaperTemplate(syllabusId, templateFiles)
      setTemplateDoc(response.data)
      setEditableBlueprint(cloneBlueprint(response.data.blueprint))
      setTemplateFiles([])
      toast.success('Paper template uploaded and blueprint extracted!')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upload paper template')
    } finally {
      setUploadingTemplate(false)
    }
  }

  const handleBlueprintMetaChange = (field, value) => {
    setEditableBlueprint((prev) => ({
      ...prev,
      [field]: field === 'title' ? value : Number(value) || 0,
    }))
  }

  const handleGroupChange = (groupIndex, field, value) => {
    setEditableBlueprint((prev) => {
      const next = cloneBlueprint(prev)
      next.question_groups[groupIndex][field] =
        field === 'unit_hint' ? value : field === 'or_with_next' ? value : Number(value) || 0
      return next
    })
  }

  const handleSubpartChange = (groupIndex, optionKey, subpartIndex, field, value) => {
    setEditableBlueprint((prev) => {
      const next = cloneBlueprint(prev)
      next.question_groups[groupIndex][optionKey].subparts[subpartIndex][field] =
        field === 'label' ? value : Number(value) || 0
      return next
    })
  }

  const addSubpart = (groupIndex, optionKey) => {
    setEditableBlueprint((prev) => {
      const next = cloneBlueprint(prev)
      if (!next.question_groups[groupIndex][optionKey]) {
        next.question_groups[groupIndex][optionKey] = { subparts: [] }
      }
      next.question_groups[groupIndex][optionKey].subparts.push({ label: '', marks: 0 })
      return next
    })
  }

  const removeSubpart = (groupIndex, optionKey, subpartIndex) => {
    setEditableBlueprint((prev) => {
      const next = cloneBlueprint(prev)
      next.question_groups[groupIndex][optionKey].subparts.splice(subpartIndex, 1)
      return next
    })
  }

  const addQuestionGroup = () => {
    setEditableBlueprint((prev) => {
      const next = cloneBlueprint(prev)
      const nextNumber = (next.question_groups?.length || 0) + 1
      next.question_groups = next.question_groups || []
      next.question_groups.push({
        question_number: nextNumber,
        unit_hint: '',
        marks: 20,
        or_with_next: false,
        primary: { subparts: [{ label: '', marks: 20 }] },
        alternative: null,
      })
      return next
    })
  }

  const removeQuestionGroup = (groupIndex) => {
    setEditableBlueprint((prev) => {
      const next = cloneBlueprint(prev)
      next.question_groups.splice(groupIndex, 1)
      next.question_groups = next.question_groups.map((group, idx) => ({
        ...group,
        question_number: idx + 1,
      }))
      return next
    })
  }

  const toggleAlternative = (groupIndex) => {
    setEditableBlueprint((prev) => {
      const next = cloneBlueprint(prev)
      const group = next.question_groups[groupIndex]
      group.alternative = group.alternative
        ? null
        : { subparts: [{ label: '', marks: group.marks || 20 }] }
      return next
    })
  }

  const handleSaveBlueprint = async () => {
    if (!editableBlueprint) return
    setSavingTemplate(true)
    try {
      const response = await questionBankAPI.updatePaperTemplate(syllabusId, editableBlueprint)
      setTemplateDoc(response.data)
      setEditableBlueprint(cloneBlueprint(response.data.blueprint))
      toast.success(response.data.validation?.is_valid ? 'Blueprint saved and validated' : 'Blueprint saved with issues to fix')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save blueprint')
    } finally {
      setSavingTemplate(false)
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

      <Card>
        <CardHeader>
          <CardTitle>Paper Template</CardTitle>
          <CardDescription>
            Upload a previous semester paper. The final generated paper will follow this extracted blueprint.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input
            type="file"
            accept=".pdf,.docx,.doc,.txt,.png,.jpg,.jpeg,.webp"
            multiple
            onChange={(e) => setTemplateFiles(Array.from(e.target.files || []))}
          />
          {templateFiles.length > 0 && (
            <p className="text-sm text-gray-600">
              {templateFiles.length} template file{templateFiles.length > 1 ? 's' : ''} selected
            </p>
          )}
          <Button onClick={handleUploadTemplate} disabled={uploadingTemplate || templateFiles.length === 0}>
            {uploadingTemplate ? 'Uploading template...' : 'Upload Paper Template'}
          </Button>

          {templateDoc && editableBlueprint && (
            <div className="rounded border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700 space-y-4">
              <p className="font-semibold text-gray-900">{templateDoc.file_name}</p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <Input
                  value={editableBlueprint.title || ''}
                  onChange={(e) => handleBlueprintMetaChange('title', e.target.value)}
                  placeholder="Exam title"
                />
                <Input
                  type="number"
                  value={editableBlueprint.total_marks || 0}
                  onChange={(e) => handleBlueprintMetaChange('total_marks', e.target.value)}
                  placeholder="Total marks"
                />
                <Input
                  type="number"
                  value={editableBlueprint.duration_minutes || 0}
                  onChange={(e) => handleBlueprintMetaChange('duration_minutes', e.target.value)}
                  placeholder="Duration (minutes)"
                />
              </div>

              <div className={`rounded border p-3 ${templateDoc.validation?.is_valid ? 'border-green-300 bg-green-50 text-green-900' : 'border-amber-300 bg-amber-50 text-amber-900'}`}>
                <p className="font-semibold mb-2">
                  {templateDoc.validation?.is_valid ? 'Blueprint validation passed' : 'Blueprint issues to fix before generation'}
                </p>
                {templateDoc.validation?.issues?.length > 0 ? (
                  <ul className="list-disc list-inside space-y-1">
                    {templateDoc.validation.issues.map((issue, idx) => (
                      <li key={idx}>
                        {issue.question_number ? `Q${issue.question_number}: ` : ''}
                        {issue.message}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No structural issues detected.</p>
                )}
              </div>

              <div className="space-y-4">
                {(editableBlueprint.question_groups || []).map((group, groupIndex) => (
                  <div key={groupIndex} className="rounded border border-gray-300 bg-white p-3 space-y-3">
                    <div className="flex flex-wrap gap-2 items-center">
                      <Input
                        type="number"
                        value={group.question_number}
                        onChange={(e) => handleGroupChange(groupIndex, 'question_number', e.target.value)}
                      />
                      <Input
                        value={group.unit_hint || ''}
                        onChange={(e) => handleGroupChange(groupIndex, 'unit_hint', e.target.value)}
                        placeholder="Unit hint"
                      />
                      <Input
                        type="number"
                        value={group.marks || 0}
                        onChange={(e) => handleGroupChange(groupIndex, 'marks', e.target.value)}
                      />
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={!!group.or_with_next}
                          onChange={(e) => handleGroupChange(groupIndex, 'or_with_next', e.target.checked)}
                        />
                        OR with next question
                      </label>
                      <Button size="sm" variant="outline" onClick={() => toggleAlternative(groupIndex)}>
                        {group.alternative ? 'Remove Internal OR' : 'Add Internal OR'}
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => removeQuestionGroup(groupIndex)}>
                        Remove Question
                      </Button>
                    </div>

                    <div className="space-y-2">
                      <p className="font-medium text-gray-900">Primary structure</p>
                      {group.primary?.subparts?.map((subpart, subpartIndex) => (
                        <div key={subpartIndex} className="grid grid-cols-1 md:grid-cols-4 gap-2">
                          <Input
                            value={subpart.label || ''}
                            onChange={(e) => handleSubpartChange(groupIndex, 'primary', subpartIndex, 'label', e.target.value)}
                            placeholder="Label"
                          />
                          <Input
                            type="number"
                            value={subpart.marks || 0}
                            onChange={(e) => handleSubpartChange(groupIndex, 'primary', subpartIndex, 'marks', e.target.value)}
                            placeholder="Marks"
                          />
                          <div className="md:col-span-2">
                            <Button size="sm" variant="outline" onClick={() => removeSubpart(groupIndex, 'primary', subpartIndex)}>
                              Remove Subpart
                            </Button>
                          </div>
                        </div>
                      ))}
                      <Button size="sm" variant="outline" onClick={() => addSubpart(groupIndex, 'primary')}>
                        Add Primary Subpart
                      </Button>
                    </div>

                    {group.alternative && (
                      <div className="space-y-2">
                        <p className="font-medium text-gray-900">Internal OR structure</p>
                        {group.alternative.subparts?.map((subpart, subpartIndex) => (
                          <div key={subpartIndex} className="grid grid-cols-1 md:grid-cols-4 gap-2">
                            <Input
                              value={subpart.label || ''}
                              onChange={(e) => handleSubpartChange(groupIndex, 'alternative', subpartIndex, 'label', e.target.value)}
                              placeholder="Label"
                            />
                            <Input
                              type="number"
                              value={subpart.marks || 0}
                              onChange={(e) => handleSubpartChange(groupIndex, 'alternative', subpartIndex, 'marks', e.target.value)}
                              placeholder="Marks"
                            />
                            <div className="md:col-span-2">
                              <Button size="sm" variant="outline" onClick={() => removeSubpart(groupIndex, 'alternative', subpartIndex)}>
                                Remove OR Subpart
                              </Button>
                            </div>
                          </div>
                        ))}
                        <Button size="sm" variant="outline" onClick={() => addSubpart(groupIndex, 'alternative')}>
                          Add OR Subpart
                        </Button>
                      </div>
                    )}

                    <p className="text-xs text-gray-500">
                      Summary: Q{group.question_number} | {group.unit_hint || 'Unit unspecified'} | {group.marks} marks
                      {group.or_with_next ? ' | OR with next question' : ''}
                      {!group.or_with_next && group.alternative ? ' | Internal OR pattern' : ''}
                      {group.primary?.subparts?.length > 0 ? ` | Primary: ${formatSubpartMarks(group.primary.subparts)}` : ''}
                      {group.alternative?.subparts?.length > 0 ? ` | OR: ${formatSubpartMarks(group.alternative.subparts)}` : ''}
                    </p>
                  </div>
                ))}
              </div>

              <div className="flex flex-wrap gap-3">
                <Button size="sm" variant="outline" onClick={addQuestionGroup}>
                  Add Question Group
                </Button>
                <Button size="sm" onClick={handleSaveBlueprint} disabled={savingTemplate || !editableBlueprint}>
                  {savingTemplate ? 'Saving blueprint...' : 'Save Blueprint Review'}
                </Button>
              </div>
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
