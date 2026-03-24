import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { syllabusAPI, questionBankAPI } from '@/api/client'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import { CheckCircle2, Filter, LibraryBig, RefreshCw, ShieldCheck, Sparkles, Upload } from 'lucide-react'

const REVIEW_STATUSES = ['pending', 'approved', 'edited', 'rejected']
const statusTone = { pending: 'secondary', approved: 'default', edited: 'secondary', rejected: 'destructive' }
const cloneBlueprint = (blueprint) => JSON.parse(JSON.stringify(blueprint || {}))
const stageTone = {
  complete: 'border-green-200 bg-green-50 text-green-900',
  current: 'border-slate-300 bg-slate-50 text-slate-900',
  pending: 'border-gray-200 bg-white text-gray-600',
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
    } catch {
      toast.error('Failed to load syllabus')
    }
  }

  const loadBank = async () => {
    setLoadingBank(true)
    try {
      const response = await questionBankAPI.listQuestionBank(syllabusId)
      setBank(response.data)
    } catch {
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
    if (!refFile) return toast.error('Please select a reference file')
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
    if (!curatedCount) return toast.error('Approve or edit some bank questions before generating a paper')
    if (!templateDoc) return toast.error('Upload a previous paper template before generating the final paper')
    if (!templateDoc.validation?.is_valid) return toast.error('Review and fix the blueprint issues before generating the final paper')
    try {
      const response = await questionBankAPI.generateQuestionPaperFromTemplate(syllabusId)
      toast.success('Question paper generated from curated bank and uploaded template!')
      navigate(`/question-paper/${response.data.id}`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate question paper')
    }
  }

  const handleUploadTemplate = async () => {
    if (!templateFiles.length) return toast.error('Please select one or more template files')
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

  const handleBlueprintMetaChange = (field, value) =>
    setEditableBlueprint((prev) => ({ ...prev, [field]: field === 'title' ? value : Number(value) || 0 }))

  const handleGroupChange = (groupIndex, field, value) =>
    setEditableBlueprint((prev) => {
      const next = cloneBlueprint(prev)
      next.question_groups[groupIndex][field] = field === 'unit_hint' ? value : field === 'or_with_next' ? value : Number(value) || 0
      return next
    })

  const handleSubpartChange = (groupIndex, optionKey, subpartIndex, field, value) =>
    setEditableBlueprint((prev) => {
      const next = cloneBlueprint(prev)
      next.question_groups[groupIndex][optionKey].subparts[subpartIndex][field] = field === 'label' ? value : Number(value) || 0
      return next
    })

  const addSubpart = (groupIndex, optionKey) =>
    setEditableBlueprint((prev) => {
      const next = cloneBlueprint(prev)
      if (!next.question_groups[groupIndex][optionKey]) next.question_groups[groupIndex][optionKey] = { subparts: [] }
      next.question_groups[groupIndex][optionKey].subparts.push({ label: '', marks: 0 })
      return next
    })

  const removeSubpart = (groupIndex, optionKey, subpartIndex) =>
    setEditableBlueprint((prev) => {
      const next = cloneBlueprint(prev)
      next.question_groups[groupIndex][optionKey].subparts.splice(subpartIndex, 1)
      return next
    })

  const addQuestionGroup = () =>
    setEditableBlueprint((prev) => {
      const next = cloneBlueprint(prev)
      next.question_groups = next.question_groups || []
      next.question_groups.push({
        question_number: next.question_groups.length + 1,
        unit_hint: '',
        marks: 20,
        or_with_next: false,
        primary: { subparts: [{ label: '', marks: 20 }] },
        alternative: null,
      })
      return next
    })

  const removeQuestionGroup = (groupIndex) =>
    setEditableBlueprint((prev) => {
      const next = cloneBlueprint(prev)
      next.question_groups.splice(groupIndex, 1)
      next.question_groups = next.question_groups.map((group, idx) => ({ ...group, question_number: idx + 1 }))
      return next
    })

  const toggleAlternative = (groupIndex) =>
    setEditableBlueprint((prev) => {
      const next = cloneBlueprint(prev)
      const group = next.question_groups[groupIndex]
      group.alternative = group.alternative ? null : { subparts: [{ label: '', marks: group.marks || 20 }] }
      return next
    })

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

  const updateQuestionInState = (updatedQuestion) => setBank((prev) => prev.map((question) => (question.id === updatedQuestion.id ? updatedQuestion : question)))

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
    if (!editingText.trim()) return toast.error('Question text cannot be empty')
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

  const curatedCount = bank.filter((q) => q.status === 'approved' || q.status === 'edited').length
  const counts = {
    approved: bank.filter((q) => q.status === 'approved').length,
    edited: bank.filter((q) => q.status === 'edited').length,
    pending: bank.filter((q) => q.status === 'pending').length,
    rejected: bank.filter((q) => q.status === 'rejected').length,
  }
  const unitOptions = [...new Set(bank.map((q) => q.unit).filter(Boolean))]
  const filteredBank = bank.filter((question) => {
    if (statusFilter !== 'all' && question.status !== statusFilter) return false
    if (unitFilter !== 'all' && question.unit !== unitFilter) return false
    if (bloomFilter !== 'all' && question.bloom_level !== bloomFilter) return false
    if (topicFilter.trim() && !question.topic.toLowerCase().includes(topicFilter.trim().toLowerCase())) return false
    return true
  })

  const workflowStages = [
    { title: 'Reference grounding', description: 'Optional retrieval support.', status: refDocs.length ? 'complete' : 'current', detail: refDocs.length ? `${refDocs.length} files uploaded` : 'No grounding files added yet' },
    { title: 'Question bank', description: 'Generate and curate the draft bank.', status: bank.length ? 'complete' : 'current', detail: bank.length ? `${bank.length} questions generated` : 'Bank not generated yet' },
    { title: 'Template blueprint', description: 'Upload and validate the template.', status: templateDoc?.validation?.is_valid ? 'complete' : templateDoc ? 'current' : 'pending', detail: templateDoc ? (templateDoc.validation?.is_valid ? 'Blueprint validated' : 'Blueprint needs review') : 'No template uploaded yet' },
    { title: 'Final paper assembly', description: 'Generate from curated questions only.', status: curatedCount && templateDoc?.validation?.is_valid ? 'current' : 'pending', detail: curatedCount ? `${curatedCount} curated questions ready` : 'Curate approved questions first' },
  ]

  const renderSubparts = (groupIndex, optionKey, subparts = [], label) => (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <p className="font-medium text-gray-900">{label}</p>
      <div className="mt-3 space-y-2">
        {subparts.map((subpart, subpartIndex) => (
          <div key={subpartIndex} className="grid grid-cols-1 gap-2 md:grid-cols-4">
            <Input value={subpart.label || ''} onChange={(e) => handleSubpartChange(groupIndex, optionKey, subpartIndex, 'label', e.target.value)} placeholder="Label" />
            <Input type="number" value={subpart.marks || 0} onChange={(e) => handleSubpartChange(groupIndex, optionKey, subpartIndex, 'marks', e.target.value)} placeholder="Marks" />
            <div className="md:col-span-2">
              <Button size="sm" variant="outline" onClick={() => removeSubpart(groupIndex, optionKey, subpartIndex)}>
                {optionKey === 'primary' ? 'Remove Subpart' : 'Remove OR Subpart'}
              </Button>
            </div>
          </div>
        ))}
      </div>
      <Button size="sm" variant="outline" className="mt-3" onClick={() => addSubpart(groupIndex, optionKey)}>
        {optionKey === 'primary' ? 'Add Primary Subpart' : 'Add OR Subpart'}
      </Button>
    </div>
  )

  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-3xl border border-slate-200 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 text-white shadow-sm">
        <div className="grid gap-6 p-6 lg:grid-cols-[1.6fr_1fr] lg:p-8">
          <div className="space-y-5">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium text-slate-100"><Sparkles size={14} />Teacher curation and paper-assembly workspace</div>
            <div>
              <h1 className="text-4xl font-bold tracking-tight">Review the bank carefully, then assemble the final paper with confidence.</h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-300">This page now follows the working teacher flow: reference grounding, question-bank curation, template review, blueprint validation, and final-paper generation.</p>
            </div>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur">
            <p className="text-sm font-semibold text-white">Current syllabus workflow</p>
            <div className="mt-4 space-y-3 text-sm text-slate-300">
              <p className="text-lg font-semibold text-white">{syllabus?.filename || 'Loading syllabus context...'}</p>
              <p>{syllabus?.topic_count || syllabus?.topics?.length || 0} units extracted</p>
              <p>Approved or edited questions are the only ones used for final-paper generation.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-3 xl:grid-cols-4">
        {workflowStages.map((stage) => (
          <div key={stage.title} className={`rounded-2xl border p-5 ${stageTone[stage.status]}`}>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] opacity-70">{stage.status === 'complete' ? 'Complete' : stage.status === 'current' ? 'Active' : 'Pending'}</p>
            <p className="mt-2 text-lg font-semibold">{stage.title}</p>
            <p className="mt-2 text-sm leading-6 opacity-80">{stage.description}</p>
            <p className="mt-4 text-sm font-medium">{stage.detail}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[{ label: 'Questions generated', value: bank.length, note: 'Draft pool available for review', icon: LibraryBig, tone: 'bg-slate-100 text-slate-900' }, { label: 'Curated for paper', value: curatedCount, note: 'Approved or edited questions', icon: CheckCircle2, tone: 'bg-green-100 text-green-900' }, { label: 'Reference files', value: refDocs.length, note: 'Grounding context in retrieval', icon: Upload, tone: 'bg-blue-100 text-blue-900' }, { label: 'Blueprint status', value: templateDoc?.validation?.is_valid ? 'Valid' : templateDoc ? 'Needs Review' : 'Missing', note: 'Generation waits for valid structure', icon: ShieldCheck, tone: 'bg-amber-100 text-amber-900' }].map(({ label, value, note, icon: Icon, tone }) => (
          <Card key={label} className="rounded-2xl border-slate-200 shadow-sm">
            <CardContent className="flex items-start gap-4 p-5">
              <div className={`rounded-2xl p-3 ${tone}`}><Icon size={22} /></div>
              <div><p className="text-sm font-medium text-gray-600">{label}</p><p className="text-3xl font-bold text-gray-900">{value}</p><p className="text-sm text-gray-600">{note}</p></div>
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <Card className="rounded-2xl border-slate-200 shadow-sm">
          <CardHeader className="pb-4"><CardTitle className="text-2xl">Reference Grounding</CardTitle><CardDescription>Add more retrieval material if you want stronger contextual support before rebuilding the bank.</CardDescription></CardHeader>
          <CardContent className="space-y-4 pt-0">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-gray-700">{refDocs.length ? `${refDocs.length} reference files uploaded.` : 'No additional reference material uploaded yet.'}</div>
            <Input type="file" accept=".pdf,.docx,.doc,.txt" onChange={(e) => setRefFile(e.target.files?.[0] || null)} />
            <Button onClick={handleUploadRef} disabled={uploadingRef || !refFile}><Upload size={16} className="mr-2" />{uploadingRef ? 'Uploading...' : 'Upload Reference Material'}</Button>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-slate-200 shadow-sm">
          <CardHeader className="pb-4"><CardTitle className="text-2xl">Question Bank Generation</CardTitle><CardDescription>Generate the first draft, then review each question before final paper assembly.</CardDescription></CardHeader>
          <CardContent className="space-y-4 pt-0">
            <div className="rounded-2xl bg-slate-50 p-4 text-sm leading-6 text-gray-700">The generator follows the extracted syllabus structure and produces Bloom-aligned questions for teacher curation.</div>
            <Button onClick={handleGenerateBank} disabled={loadingBank}>{loadingBank ? 'Generating question bank...' : 'Generate Question Bank'}</Button>
            <div className="grid gap-3 sm:grid-cols-4">{Object.entries(counts).map(([key, value]) => <div key={key} className="rounded-xl border border-slate-200 p-3 text-sm"><p className="font-semibold text-gray-900">{value}</p><p className="capitalize text-gray-600">{key}</p></div>)}</div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.05fr_1.45fr]">
        <Card className="rounded-2xl border-slate-200 shadow-sm">
          <CardHeader className="pb-4"><CardTitle className="text-2xl">Template and Blueprint Review</CardTitle><CardDescription>Upload a previous paper, extract its structure, then validate it before final-paper generation.</CardDescription></CardHeader>
          <CardContent className="space-y-4 pt-0">
            <Input type="file" accept=".pdf,.docx,.doc,.txt,.png,.jpg,.jpeg,.webp" multiple onChange={(e) => setTemplateFiles(Array.from(e.target.files || []))} />
            {templateFiles.length > 0 ? <p className="text-sm text-gray-600">{templateFiles.length} template file{templateFiles.length > 1 ? 's' : ''} selected</p> : null}
            <Button onClick={handleUploadTemplate} disabled={uploadingTemplate || !templateFiles.length}>{uploadingTemplate ? 'Uploading template...' : 'Upload Paper Template'}</Button>
            <div className={`rounded-2xl border p-4 text-sm ${templateDoc?.validation?.is_valid ? 'border-green-200 bg-green-50 text-green-900' : 'border-slate-200 bg-slate-50 text-gray-700'}`}>
              <p className="font-semibold text-gray-900">{templateDoc?.file_name || 'No template uploaded yet'}</p>
              <p className="mt-1">{templateDoc ? (templateDoc.validation?.is_valid ? 'Blueprint validation passed.' : 'Blueprint review still has issues to fix.') : 'Upload a previous paper or raw images to begin blueprint extraction.'}</p>
              {templateDoc?.validation?.issues?.length > 0 ? <ul className="mt-2 list-inside list-disc space-y-1">{templateDoc.validation.issues.map((issue, idx) => <li key={idx}>{issue.question_number ? `Q${issue.question_number}: ` : ''}{issue.message}</li>)}</ul> : null}
            </div>
            <Button variant={curatedCount > 0 && templateDoc?.validation?.is_valid ? 'default' : 'outline'} onClick={handleGeneratePaper} disabled={!bank.length}>Generate Question Paper from Curated Bank</Button>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-slate-200 shadow-sm">
          <CardHeader className="pb-4"><CardTitle className="text-2xl">Editable Blueprint</CardTitle><CardDescription>Adjust template metadata, subparts, OR behavior, and question groups here.</CardDescription></CardHeader>
          <CardContent className="pt-0">
            {!templateDoc || !editableBlueprint ? <div className="rounded-2xl border border-dashed border-slate-300 p-6 text-sm text-gray-500">Upload a template first to unlock blueprint review.</div> : (
              <div className="space-y-4">
                <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                  <Input value={editableBlueprint.title || ''} onChange={(e) => handleBlueprintMetaChange('title', e.target.value)} placeholder="Exam title" />
                  <Input type="number" value={editableBlueprint.total_marks || 0} onChange={(e) => handleBlueprintMetaChange('total_marks', e.target.value)} placeholder="Total marks" />
                  <Input type="number" value={editableBlueprint.duration_minutes || 0} onChange={(e) => handleBlueprintMetaChange('duration_minutes', e.target.value)} placeholder="Duration (minutes)" />
                </div>
                <div className="max-h-[760px] space-y-4 overflow-y-auto pr-1">
                  {(editableBlueprint.question_groups || []).map((group, groupIndex) => (
                    <div key={groupIndex} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <Input type="number" value={group.question_number} onChange={(e) => handleGroupChange(groupIndex, 'question_number', e.target.value)} />
                        <Input value={group.unit_hint || ''} onChange={(e) => handleGroupChange(groupIndex, 'unit_hint', e.target.value)} placeholder="Unit hint" />
                        <Input type="number" value={group.marks || 0} onChange={(e) => handleGroupChange(groupIndex, 'marks', e.target.value)} placeholder="Marks" />
                        <label className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-gray-700"><input type="checkbox" checked={!!group.or_with_next} onChange={(e) => handleGroupChange(groupIndex, 'or_with_next', e.target.checked)} />OR with next question</label>
                        <Button size="sm" variant="outline" onClick={() => toggleAlternative(groupIndex)}>{group.alternative ? 'Remove Internal OR' : 'Add Internal OR'}</Button>
                        <Button size="sm" variant="outline" onClick={() => removeQuestionGroup(groupIndex)}>Remove Question</Button>
                      </div>
                      <div className="mt-4 space-y-3">
                        {renderSubparts(groupIndex, 'primary', group.primary?.subparts || [], 'Primary structure')}
                        {group.alternative ? renderSubparts(groupIndex, 'alternative', group.alternative.subparts || [], 'Internal OR structure') : null}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex flex-wrap gap-3">
                  <Button size="sm" variant="outline" onClick={addQuestionGroup}>Add Question Group</Button>
                  <Button size="sm" onClick={handleSaveBlueprint} disabled={savingTemplate || !editableBlueprint}>{savingTemplate ? 'Saving blueprint...' : 'Save Blueprint Review'}</Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      {bank.length > 0 ? (
        <>
          <Card className="rounded-2xl border-slate-200 shadow-sm">
            <CardHeader className="pb-4"><div className="flex flex-wrap items-center justify-between gap-4"><div><CardTitle className="text-2xl">Question Review Filters</CardTitle><CardDescription>Narrow the bank by review state, unit, Bloom level, or topic before approving the final pool.</CardDescription></div><div className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-700"><Filter size={14} />Review controls</div></div></CardHeader>
            <CardContent className="grid grid-cols-1 gap-3 pt-0 md:grid-cols-4">
              <select className="rounded-md border border-gray-300 px-3 py-2 text-sm" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}><option value="all">All statuses</option>{REVIEW_STATUSES.map((status) => <option key={status} value={status}>{status}</option>)}</select>
              <select className="rounded-md border border-gray-300 px-3 py-2 text-sm" value={unitFilter} onChange={(e) => setUnitFilter(e.target.value)}><option value="all">All units</option>{unitOptions.map((unit) => <option key={unit} value={unit}>{unit}</option>)}</select>
              <select className="rounded-md border border-gray-300 px-3 py-2 text-sm" value={bloomFilter} onChange={(e) => setBloomFilter(e.target.value)}><option value="all">All Bloom levels</option><option value="Remember">Remember</option><option value="Apply">Apply</option><option value="Analyze">Analyze</option></select>
              <Input placeholder="Filter by topic" value={topicFilter} onChange={(e) => setTopicFilter(e.target.value)} />
            </CardContent>
          </Card>

          <Card className="rounded-2xl border-slate-200 shadow-sm">
            <CardHeader className="pb-4"><div className="flex flex-wrap items-center justify-between gap-4"><div><CardTitle className="text-2xl">Curate Bank Questions</CardTitle><CardDescription>Approve, reject, edit, or regenerate questions before you assemble the final paper.</CardDescription></div><div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-700">{filteredBank.length} visible</div></div></CardHeader>
            <CardContent className="max-h-[760px] space-y-4 overflow-y-auto pt-0">
              {filteredBank.map((q) => {
                const isEditing = editingId === q.id
                const isBusy = busyQuestionId === q.id
                return (
                  <div key={q.id} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge>{q.bloom_level}</Badge>
                      <Badge variant="secondary">{q.difficulty}</Badge>
                      <Badge variant={statusTone[q.status] || 'secondary'}>{q.status}</Badge>
                      {q.unit ? <span className="ml-auto text-xs text-gray-500">Unit: {q.unit}</span> : null}
                    </div>
                    <div className="mt-4">{isEditing ? <textarea className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm" rows={4} value={editingText} onChange={(e) => setEditingText(e.target.value)} /> : <p className="text-sm font-medium leading-7 text-gray-900">{q.question}</p>}</div>
                    <div className="mt-3 text-xs text-gray-600">{q.topic ? <p>Topic: {q.topic}</p> : null}<p className="mt-1">Only approved and edited questions are eligible for final-paper generation.</p></div>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {isEditing ? (
                        <>
                          <Button size="sm" onClick={() => handleSaveEdit(q.id)} disabled={isBusy}>{isBusy ? 'Saving...' : 'Save Edit'}</Button>
                          <Button size="sm" variant="outline" onClick={() => { setEditingId(''); setEditingText('') }} disabled={isBusy}>Cancel</Button>
                        </>
                      ) : (
                        <>
                          <Button size="sm" onClick={() => handleStatusUpdate(q.id, 'approved')} disabled={isBusy}>Approve</Button>
                          <Button size="sm" variant="outline" onClick={() => handleStatusUpdate(q.id, 'rejected')} disabled={isBusy}>Reject</Button>
                          <Button size="sm" variant="outline" onClick={() => { setEditingId(q.id); setEditingText(q.question) }} disabled={isBusy}>Edit</Button>
                          <Button size="sm" variant="outline" onClick={() => handleRegenerateQuestion(q.id)} disabled={isBusy}><RefreshCw size={14} className="mr-2" />{isBusy ? 'Regenerating...' : 'Regenerate'}</Button>
                        </>
                      )}
                    </div>
                  </div>
                )
              })}
              {filteredBank.length === 0 ? <div className="py-8 text-center text-sm text-gray-500">No questions match the current filters.</div> : null}
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  )
}

export default QuestionBankPage
