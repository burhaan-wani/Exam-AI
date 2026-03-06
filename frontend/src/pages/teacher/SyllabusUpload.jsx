import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { questionBankAPI } from '@/api/client'
import Button from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Upload, FileText, CheckCircle } from 'lucide-react'

const SyllabusUpload = () => {
  const navigate = useNavigate()
  const [syllabusFile, setSyllabusFile] = useState(null)
  const [refFiles, setRefFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [units, setUnits] = useState(null)
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  const handleSyllabusChange = (e) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setSyllabusFile(selectedFile)
      setUnits(null)
    }
  }

  const handleRefFilesChange = (e) => {
    const files = Array.from(e.target.files || [])
    setRefFiles(files)
  }

  const handleUpload = async () => {
    if (!syllabusFile) {
      toast.error('Please select a syllabus file')
      return
    }

    setLoading(true)
    try {
      // Step 1: upload syllabus via new two-stage pipeline endpoint
      const response = await questionBankAPI.uploadSyllabus(syllabusFile, user.id)
      const { id, units: extractedUnits } = response.data

      setUnits(extractedUnits)
      toast.success('Syllabus uploaded and units extracted!')

      // Step 2: upload all selected reference materials (if any)
      if (refFiles.length > 0) {
        for (const file of refFiles) {
          // eslint-disable-next-line no-await-in-loop
          await questionBankAPI.uploadReferenceMaterial(id, file)
        }
        toast.success('Reference materials uploaded!')
      }

      // Step 3: navigate to question bank for this syllabus
      navigate(`/question-bank/${id}`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Syllabus & Course Material</h1>
        <p className="text-gray-600">
          Upload your course syllabus. Supported formats: PDF, DOCX, TXT
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Syllabus File</CardTitle>
          <CardDescription>Select a syllabus document to process</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* File Input */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-slate-900 transition-colors cursor-pointer"
            onClick={() => document.getElementById('syllabus-input').click()}
          >
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-2" />
            <p className="font-semibold text-gray-900 mb-1">
              {syllabusFile ? syllabusFile.name : 'Click to select or drag and drop'}
            </p>
            <p className="text-sm text-gray-600">
              PDF, DOCX, or TXT files up to 50MB
            </p>
            <input
              id="syllabus-input"
              type="file"
              accept=".pdf,.docx,.doc,.txt"
              onChange={handleSyllabusChange}
              className="hidden"
            />
          </div>

          {/* Reference Materials */}
          <div className="space-y-2">
            <h3 className="font-semibold text-gray-900">Reference Materials (optional)</h3>
            <p className="text-sm text-gray-600">
              Upload textbooks, lecture notes, or previous papers. These will be used as context for
              question generation (RAG).
            </p>
            <input
              id="ref-input"
              type="file"
              accept=".pdf,.docx,.doc,.txt"
              multiple
              onChange={handleRefFilesChange}
            />
            {refFiles.length > 0 && (
              <p className="text-xs text-gray-600">{refFiles.length} reference files selected</p>
            )}
          </div>

          {/* Units Preview */}
          {units && (
            <div className="space-y-2">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                Extracted Units ({units.length})
              </h3>
              <div className="max-h-96 overflow-y-auto space-y-2 p-4 bg-gray-50 rounded-lg">
                {units.map((unit, idx) => (
                  <div key={idx} className="text-sm">
                    <p className="font-semibold text-gray-900">{unit}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <Button
              onClick={handleUpload}
              disabled={!syllabusFile || loading}
              className="flex-1"
            >
              {loading ? 'Processing...' : 'Process Syllabus'}
            </Button>
            {syllabusFile && !units && (
              <Button
                variant="outline"
                onClick={() => {
                  setSyllabusFile(null)
                  setUnits(null)
                  setRefFiles([])
                }}
              >
                Clear
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Info */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <h4 className="font-semibold text-blue-900 mb-2">What happens next?</h4>
          <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
            <li>Units are extracted from your syllabus using AI analysis</li>
            <li>Reference materials are indexed for retrieval-augmented generation</li>
            <li>An AI-generated question bank is created across Bloom levels for each unit</li>
            <li>You can review the bank and then generate a question paper from it</li>
          </ol>
        </CardContent>
      </Card>
    </div>
  )
}

export default SyllabusUpload
