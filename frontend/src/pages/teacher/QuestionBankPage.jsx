import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { syllabusAPI, questionBankAPI } from '@/api/client'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'

const QuestionBankPage = () => {
  const { syllabusId } = useParams()
  const navigate = useNavigate()
  const [syllabus, setSyllabus] = useState(null)
  const [bank, setBank] = useState([])
  const [loadingBank, setLoadingBank] = useState(false)
  const [uploadingRef, setUploadingRef] = useState(false)
  const [refFile, setRefFile] = useState(null)
  const [refDocs, setRefDocs] = useState([])

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
      // empty bank is fine; just show nothing
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
      toast.success(`Generated ${response.data.length} questions in bank`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate question bank')
    } finally {
      setLoadingBank(false)
    }
  }

  const handleGeneratePaper = async () => {
    if (bank.length === 0) {
      toast.error('Generate a question bank first')
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
      toast.success('Question paper generated from question bank!')
      navigate(`/question-paper/${response.data.id}`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate question paper')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Question Bank</h1>
        <p className="text-gray-600">
          Generate and manage a question bank for this syllabus, then build a question paper from it.
        </p>
      </div>

      {syllabus && (
        <Card>
          <CardHeader>
            <CardTitle>{syllabus.filename}</CardTitle>
            <CardDescription>
              {syllabus.topics?.length || 0} topics • Uploaded{' '}
              {new Date(syllabus.created_at).toLocaleDateString()}
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      {/* Reference Material Upload */}
      <Card>
        <CardHeader>
          <CardTitle>Add More Reference Material (Optional)</CardTitle>
          <CardDescription>
            You already upload course material on the Upload Syllabus page. Use this only if you want
            to add more files later for better RAG grounding.
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
              {refDocs.length > 8 && (
                <p className="text-xs text-gray-500 mt-1">…and {refDocs.length - 8} more</p>
              )}
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

      {/* Question Bank Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Generate Question Bank</CardTitle>
          <CardDescription>
            AI will generate a structured question bank across Bloom levels for each course unit.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button onClick={handleGenerateBank} disabled={loadingBank}>
            {loadingBank ? 'Generating question bank...' : 'Generate Question Bank'}
          </Button>

          {bank.length > 0 && (
            <div className="flex justify-between items-center mt-2">
              <span className="text-sm text-gray-600">
                {bank.length} questions in bank
              </span>
              <Button variant="outline" onClick={handleGeneratePaper}>
                Generate Question Paper from Bank
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Question Bank List */}
      {bank.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Bank Questions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 max-h-[480px] overflow-y-auto">
            {bank.map((q) => (
              <div key={q.id} className="border rounded p-3 space-y-1">
                <div className="flex items-center gap-2">
                  <Badge>{q.bloom_level}</Badge>
                  <Badge variant="secondary">{q.difficulty}</Badge>
                  {q.unit && (
                    <span className="ml-auto text-xs text-gray-500">Unit: {q.unit}</span>
                  )}
                </div>
                <p className="text-sm font-medium text-gray-900">{q.question}</p>
                {q.topic && (
                  <p className="text-xs text-gray-600">Topic: {q.topic}</p>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default QuestionBankPage

