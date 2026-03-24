import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { questionBankAPI } from '@/api/client'
import Button from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import {
  BookOpen,
  CheckCircle,
  ChevronRight,
  FileSearch,
  FileStack,
  LibraryBig,
  Upload,
} from 'lucide-react'

const workflowSteps = [
  {
    title: 'Upload syllabus',
    description: 'Extract a reliable unit and subtopic structure from the source document.',
    icon: Upload,
  },
  {
    title: 'Add reference material',
    description: 'Store grounding documents in retrieval so question generation has better context.',
    icon: BookOpen,
  },
  {
    title: 'Review extracted structure',
    description: 'Confirm the course outline before moving into question-bank generation.',
    icon: FileSearch,
  },
  {
    title: 'Continue to curation',
    description: 'Move into bank review, blueprint setup, and final paper assembly.',
    icon: LibraryBig,
  },
]

const SyllabusUpload = () => {
  const navigate = useNavigate()
  const [syllabusFile, setSyllabusFile] = useState(null)
  const [refFiles, setRefFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [units, setUnits] = useState(null)
  const [topicsByUnit, setTopicsByUnit] = useState(null)
  const [syllabusId, setSyllabusId] = useState(null)
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  const handleSyllabusChange = (e) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setSyllabusFile(selectedFile)
      setSyllabusId(null)
      setUnits(null)
      setTopicsByUnit(null)
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
      const response = await questionBankAPI.uploadSyllabus(syllabusFile, user.id)
      const { id, units: extractedUnits, topics } = response.data

      setSyllabusId(id)
      setUnits(extractedUnits)
      setTopicsByUnit(topics || [])
      toast.success('Syllabus uploaded and units extracted!')

      if (refFiles.length > 0) {
        for (const file of refFiles) {
          // eslint-disable-next-line no-await-in-loop
          await questionBankAPI.uploadReferenceMaterial(id, file)
        }
        toast.success('Reference materials uploaded!')
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  const extractedUnitCount = topicsByUnit?.length || units?.length || 0

  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-3xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 shadow-sm">
        <div className="grid gap-5 p-6 lg:grid-cols-[1.5fr_1fr] lg:p-8">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-700">
              Teacher Workflow
            </div>
            <div>
              <h1 className="text-4xl font-bold tracking-tight text-gray-900">Start with the syllabus, then let the workflow branch naturally.</h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-gray-600">
                This stage creates the structured foundation for the rest of the teacher experience. Once the syllabus is parsed,
                you can ground generation with references, review extracted units, and continue into question-bank curation.
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-semibold text-gray-900">Why this stage matters</p>
            <div className="mt-4 space-y-3 text-sm leading-6 text-gray-600">
              <div className="rounded-xl bg-slate-50 p-3">The syllabus defines the course structure used for all later question selection.</div>
              <div className="rounded-xl bg-slate-50 p-3">Reference material improves the grounding quality of the generated bank.</div>
              <div className="rounded-xl bg-slate-50 p-3">The extracted outline gives teachers a quick validation checkpoint before generation starts.</div>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.35fr_1fr]">
        <Card className="rounded-2xl border-slate-200 shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-2xl">Upload Course Files</CardTitle>
            <CardDescription>Choose the syllabus first, then optionally add grounding material in the same step.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5 pt-0">
            <div
              className="rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 p-10 text-center transition-colors hover:border-slate-900"
              onClick={() => document.getElementById('syllabus-input').click()}
            >
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-sm">
                <Upload className="h-8 w-8 text-slate-700" />
              </div>
              <p className="mt-4 text-lg font-semibold text-gray-900">
                {syllabusFile ? syllabusFile.name : 'Select the syllabus file'}
              </p>
              <p className="mt-2 text-sm text-gray-600">Supports PDF, DOCX, DOC, and TXT up to 50MB.</p>
              <input
                id="syllabus-input"
                type="file"
                accept=".pdf,.docx,.doc,.txt"
                onChange={handleSyllabusChange}
                className="hidden"
              />
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5">
              <div className="flex items-start gap-3">
                <div className="rounded-xl bg-slate-100 p-3 text-slate-900">
                  <FileStack size={20} />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">Reference materials</h3>
                  <p className="mt-1 text-sm leading-6 text-gray-600">
                    Upload lecture notes, textbooks, or prior papers. These will be indexed for retrieval and used to ground question generation.
                  </p>
                </div>
              </div>
              <div className="mt-4 space-y-3">
                <input
                  id="ref-input"
                  type="file"
                  accept=".pdf,.docx,.doc,.txt"
                  multiple
                  onChange={handleRefFilesChange}
                  className="block w-full text-sm text-gray-700 file:mr-4 file:rounded-lg file:border-0 file:bg-slate-900 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-slate-800"
                />
                <p className="text-xs text-gray-500">
                  {refFiles.length > 0 ? `${refFiles.length} reference file${refFiles.length > 1 ? 's' : ''} selected` : 'No reference files selected yet.'}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button onClick={handleUpload} disabled={!syllabusFile || loading} className="min-w-[200px]">
                {loading ? 'Processing...' : 'Process Syllabus'}
              </Button>
              {(syllabusFile || refFiles.length > 0 || units) ? (
                <Button
                  variant="outline"
                  onClick={() => {
                    setSyllabusFile(null)
                    setSyllabusId(null)
                    setUnits(null)
                    setTopicsByUnit(null)
                    setRefFiles([])
                  }}
                >
                  Reset Selection
                </Button>
              ) : null}
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-slate-200 shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-2xl">Workflow Preview</CardTitle>
            <CardDescription>What the teacher flow looks like after this stage succeeds.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 pt-0">
            {workflowSteps.map(({ title, description, icon: Icon }, index) => (
              <div key={title} className="flex gap-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white text-slate-900 shadow-sm">
                  <Icon size={18} />
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Step {index + 1}</p>
                  <p className="mt-1 font-semibold text-gray-900">{title}</p>
                  <p className="mt-1 text-sm leading-6 text-gray-600">{description}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
        <Card className="rounded-2xl border-slate-200 shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-2xl">Extraction Preview</CardTitle>
            <CardDescription>Use this as a quick validation checkpoint before you continue to question-bank generation.</CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            {units ? (
              <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-green-200 bg-green-50 p-4 text-sm text-green-900">
                  <CheckCircle className="h-5 w-5" />
                  <span className="font-semibold">Extraction complete</span>
                  <span>{extractedUnitCount} unit group{extractedUnitCount === 1 ? '' : 's'} ready for review</span>
                </div>

                <div className="max-h-[520px] space-y-3 overflow-y-auto rounded-2xl bg-slate-50 p-4">
                  {(topicsByUnit || []).length > 0 ? (
                    topicsByUnit.map((unit, idx) => (
                      <div key={idx} className="rounded-2xl border border-slate-200 bg-white p-4">
                        <p className="font-semibold text-gray-900">{unit.unit}</p>
                        {unit.subtopics?.length > 0 ? (
                          <div className="mt-3 flex flex-wrap gap-2">
                            {unit.subtopics.map((topic, topicIdx) => (
                              <span key={`${idx}-${topicIdx}`} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                                {topic}
                              </span>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    ))
                  ) : (
                    units.map((unit, idx) => (
                      <div key={idx} className="rounded-2xl border border-slate-200 bg-white p-4 text-sm font-semibold text-gray-900">
                        {unit}
                      </div>
                    ))
                  )}
                </div>
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-300 p-10 text-center text-sm text-gray-500">
                Upload and process a syllabus to preview the extracted units and subtopics here.
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-slate-200 shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-2xl">Next Stage</CardTitle>
            <CardDescription>The handoff from syllabus ingestion into the question-bank workspace.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 pt-0">
            <div className="rounded-2xl bg-slate-50 p-4 text-sm leading-6 text-gray-700">
              After this step, the teacher workflow moves into question-bank generation, reference refinement, template upload,
              blueprint review, and final paper assembly.
            </div>
            <div className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4">
              <div className="flex items-center gap-3">
                <div className="rounded-xl bg-slate-100 p-2 text-slate-900">
                  <ChevronRight size={18} />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">Continue to question bank</p>
                  <p className="text-sm text-gray-600">Start curation only after the syllabus structure looks right.</p>
                </div>
              </div>
              <Button
                variant={syllabusId ? 'default' : 'outline'}
                className="w-full"
                onClick={() => syllabusId && navigate(`/question-bank/${syllabusId}`)}
                disabled={!syllabusId}
              >
                {syllabusId ? 'Continue to Question Bank' : 'Process a syllabus first'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}

export default SyllabusUpload
