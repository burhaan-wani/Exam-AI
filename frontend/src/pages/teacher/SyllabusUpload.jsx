import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { syllabusAPI } from '@/api/client'
import Button from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Upload, FileText, CheckCircle } from 'lucide-react'

const SyllabusUpload = () => {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [topics, setTopics] = useState(null)
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      setTopics(null)
    }
  }

  const handleUpload = async () => {
    if (!file) {
      toast.error('Please select a file')
      return
    }

    setLoading(true)
    try {
      const response = await syllabusAPI.upload(file, user.id)
      const { id, topics: extractedTopics } = response.data

      setTopics(extractedTopics)
      toast.success('Syllabus uploaded and processed!')

      setTimeout(() => {
        navigate(`/configure-bloom/${id}`)
      }, 1500)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Syllabus</h1>
        <p className="text-gray-600">
          Upload your course syllabus. Supported formats: PDF, DOCX, TXT
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Choose File</CardTitle>
          <CardDescription>Select a syllabus document to process</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* File Input */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-slate-900 transition-colors cursor-pointer"
            onClick={() => document.getElementById('file-input').click()}
          >
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-2" />
            <p className="font-semibold text-gray-900 mb-1">
              {file ? file.name : 'Click to select or drag and drop'}
            </p>
            <p className="text-sm text-gray-600">
              PDF, DOCX, or TXT files up to 50MB
            </p>
            <input
              id="file-input"
              type="file"
              accept=".pdf,.docx,.doc,.txt"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>

          {/* Topics Preview */}
          {topics && (
            <div className="space-y-2">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                Extracted Topics ({topics.length})
              </h3>
              <div className="max-h-96 overflow-y-auto space-y-2 p-4 bg-gray-50 rounded-lg">
                {topics.map((topic, idx) => (
                  <div key={idx} className="text-sm">
                    <p className="font-semibold text-gray-900">{topic.name}</p>
                    {topic.unit && (
                      <p className="text-xs text-gray-600">Unit: {topic.unit}</p>
                    )}
                    {topic.subtopics?.length > 0 && (
                      <p className="text-xs text-gray-600">
                        Subtopics: {topic.subtopics.join(', ')}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <Button
              onClick={handleUpload}
              disabled={!file || loading}
              className="flex-1"
            >
              {loading ? 'Processing...' : 'Process Syllabus'}
            </Button>
            {file && !topics && (
              <Button
                variant="outline"
                onClick={() => {
                  setFile(null)
                  setTopics(null)
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
            <li>Topics are extracted using AI analysis</li>
            <li>You'll configure Bloom's Taxonomy levels per topic</li>
            <li>Questions will be generated based on your configuration</li>
            <li>You can review and refine each question</li>
            <li>Finally, your question paper will be assembled</li>
          </ol>
        </CardContent>
      </Card>
    </div>
  )
}

export default SyllabusUpload
