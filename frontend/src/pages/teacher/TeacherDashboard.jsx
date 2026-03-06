import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { syllabusAPI } from '@/api/client'
import Button from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import { FileText, Upload, Settings, Sparkles, ClipboardList } from 'lucide-react'

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

  const steps = [
    {
      num: 1,
      title: 'Upload Syllabus',
      description: 'Upload your course syllabus (PDF, DOCX, or TXT)',
      path: '/upload-syllabus',
      icon: Upload,
    },
    {
      num: 2,
      title: 'Question Bank',
      description: 'Generate and manage AI question banks',
      path: '/dashboard', // syllabus-specific links are shown below
      icon: Sparkles,
    },
    {
      num: 3,
      title: 'Generate Paper',
      description: 'Build papers from the question bank',
      path: '/dashboard',
      icon: FileText,
    },
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Teacher Dashboard</h1>
        <p className="text-gray-600">Welcome, {user.name}! Manage your exam papers here.</p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {steps.map(({ num, title, path, icon: Icon }) => (
          <Link key={num} to={path}>
            <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer">
              <CardContent className="p-4 flex flex-col items-center text-center">
                <div className="mb-3 p-3 bg-slate-100 rounded-lg">
                  <Icon className="w-6 h-6 text-slate-900" />
                </div>
                <span className="inline-block mb-2 text-xs font-bold text-slate-500">Step {num}</span>
                <h3 className="font-semibold text-gray-900 text-sm">{title}</h3>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Syllabi List */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Your Syllabi</h2>
        {loading ? (
          <div className="text-center text-gray-500 py-8">Loading...</div>
        ) : syllabi.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">No syllabi uploaded yet</p>
              <Link to="/upload-syllabus">
                <Button>Upload Your First Syllabus</Button>
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
                    {syllabus.topic_count} topics • {new Date(syllabus.created_at).toLocaleDateString()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-2">
                    <Link to={`/question-bank/${syllabus.id}`} className="flex-1">
                      <Button variant="secondary" className="w-full text-sm">
                        Question Bank
                      </Button>
                    </Link>
                    <Link to={`/upload-syllabus?view=${syllabus.id}`} className="flex-1">
                      <Button variant="outline" className="w-full text-sm">
                        View
                      </Button>
                    </Link>
                  </div>
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
