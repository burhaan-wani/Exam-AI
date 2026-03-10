import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { syllabusAPI } from '@/api/client'
import Button from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { FileText, Upload, LibraryBig, ArrowRight } from 'lucide-react'

const TeacherDashboard = () => {
  const [syllabi, setSyllabi] = useState([])
  const [loading, setLoading] = useState(true)
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  useEffect(() => {
    loadSyllabi()
  }, [])

  const loadSyllabi = async () => {
    try {
      const response = await syllabusAPI.list(user.id)
      setSyllabi(response.data)
    } catch (error) {
      toast.error('Failed to load syllabi')
    } finally {
      setLoading(false)
    }
  }

  const workflowCards = [
    {
      title: '1. Upload syllabus',
      description: 'Add the syllabus and any supporting material you want the generator to use.',
      icon: Upload,
      action: '/upload-syllabus',
      actionLabel: 'Upload files',
    },
    {
      title: '2. Build question bank',
      description: 'Generate a bank of Bloom-aligned questions for each extracted unit.',
      icon: LibraryBig,
      action: syllabi[0] ? `/question-bank/${syllabi[0].id}` : '/upload-syllabus',
      actionLabel: syllabi[0] ? 'Open latest bank' : 'Start with a syllabus',
    },
    {
      title: '3. Assemble and refine paper',
      description: 'Create a paper from the bank, then replace any question you do not like in the final view.',
      icon: FileText,
      action: syllabi[0] ? `/question-bank/${syllabi[0].id}` : '/upload-syllabus',
      actionLabel: 'Continue workflow',
    },
  ]

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Teacher Dashboard</h1>
          <p className="text-gray-600">Welcome, {user.name}! The teacher workflow now runs entirely through the question bank pipeline.</p>
        </div>
        <Link to="/upload-syllabus">
          <Button>
            <Upload size={18} className="mr-2" />
            New syllabus
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {workflowCards.map(({ title, description, icon: Icon, action, actionLabel }) => (
          <Card key={title} className="h-full">
            <CardHeader>
              <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center mb-3">
                <Icon className="w-6 h-6 text-slate-900" />
              </div>
              <CardTitle className="text-xl">{title}</CardTitle>
              <CardDescription>{description}</CardDescription>
            </CardHeader>
            <CardContent>
              <Link to={action}>
                <Button variant="outline" className="w-full justify-between">
                  {actionLabel}
                  <ArrowRight size={16} />
                </Button>
              </Link>
            </CardContent>
          </Card>
        ))}
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Your syllabi</h2>
            <p className="text-sm text-gray-600">Each syllabus is an entry point into the new teacher workflow.</p>
          </div>
        </div>

        {loading ? (
          <div className="text-center text-gray-500 py-8">Loading...</div>
        ) : syllabi.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">No syllabi uploaded yet.</p>
              <Link to="/upload-syllabus">
                <Button>Upload your first syllabus</Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {syllabi.map((syllabus) => (
              <Card key={syllabus.id}>
                <CardHeader>
                  <CardTitle className="text-lg">{syllabus.filename}</CardTitle>
                  <CardDescription>
                    {syllabus.topic_count} units extracted
                    {syllabus.created_at ? ` • ${new Date(syllabus.created_at).toLocaleDateString()}` : ''}
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex gap-3">
                  <Link to={`/question-bank/${syllabus.id}`} className="flex-1">
                    <Button className="w-full">Open question bank</Button>
                  </Link>
                  <Link to="/upload-syllabus" className="flex-1">
                    <Button variant="outline" className="w-full">Upload more files</Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default TeacherDashboard
