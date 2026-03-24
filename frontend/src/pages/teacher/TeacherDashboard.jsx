import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { syllabusAPI } from '@/api/client'
import Button from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { ArrowRight, CheckCircle2, FileText, LibraryBig, Upload } from 'lucide-react'

const formatDate = (value) => {
  if (!value) return 'Recently'
  return new Date(value).toLocaleDateString()
}

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
    } catch {
      toast.error('Failed to load syllabus files')
    } finally {
      setLoading(false)
    }
  }

  const latestSyllabus = syllabi[0]
  const totalUnits = syllabi.reduce((sum, syllabus) => sum + (syllabus.topic_count || 0), 0)
  const latestWorkflowComplete = latestSyllabus?.latest_final_paper_status === 'finalized'

  const stats = [
    {
      label: 'Syllabus files',
      value: syllabi.length,
      note: 'Available teacher workflows',
      icon: FileText,
    },
    {
      label: 'Units extracted',
      value: totalUnits,
      note: 'Available for bank generation',
      icon: LibraryBig,
    },
    {
      label: 'Status',
      value: latestWorkflowComplete ? 'Completed' : latestSyllabus ? 'In Progress' : 'Ready',
      note: latestWorkflowComplete
        ? 'The latest workflow has a finalized paper'
        : latestSyllabus
          ? 'You can continue the latest workflow'
          : 'Start by uploading a syllabus',
      icon: CheckCircle2,
    },
  ]

  const quickActions = [
    {
      title: 'Start New Workflow',
      description: 'Upload a syllabus and optional reference material.',
      action: '/upload-syllabus',
      actionLabel: 'Upload syllabus',
    },
    {
      title: 'Continue Latest Workflow',
      description: latestSyllabus
        ? latestWorkflowComplete
          ? `Review the completed workflow for ${latestSyllabus.filename}`
          : `Resume work on ${latestSyllabus.filename}`
        : 'No active workflow yet. Start with a new upload.',
      action: latestSyllabus ? `/question-bank/${latestSyllabus.id}` : '/upload-syllabus',
      actionLabel: latestSyllabus ? (latestWorkflowComplete ? 'View workflow' : 'Open workflow') : 'Start now',
    },
  ]

  return (
    <div className="space-y-5">
      <section className="grid gap-4 lg:grid-cols-[1.45fr_1fr]">
        <Card className="rounded-2xl border-slate-200 shadow-sm">
          <CardContent className="p-7 lg:p-8">
            <div className="max-w-3xl">
              <h1 className="text-3xl font-bold tracking-tight text-slate-900">Teacher Dashboard</h1>
              <p className="mt-3 text-sm leading-6 text-slate-600">
                Manage the full teacher flow from syllabus upload to final paper approval. Start a new workflow or continue the latest one without digging through extra screens.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link to="/upload-syllabus">
                  <Button>
                    <Upload size={16} className="mr-2" />
                    New Workflow
                  </Button>
                </Link>
                {latestSyllabus ? (
                  <Link to={`/question-bank/${latestSyllabus.id}`}>
                    <Button variant="outline">
                      Continue Latest
                      <ArrowRight size={16} className="ml-2" />
                    </Button>
                  </Link>
                ) : null}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-slate-200 shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl">Latest Workflow</CardTitle>
            <CardDescription>Pick up where you left off.</CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            {latestSyllabus ? (
              <div className="space-y-4">
                <div className="rounded-xl bg-slate-50 p-4">
                  <p className="font-semibold text-slate-900">{latestSyllabus.filename}</p>
                  <p className="mt-1 text-sm text-slate-600">
                    {latestSyllabus.topic_count || 0} units extracted on {formatDate(latestSyllabus.created_at)}
                  </p>
                  <p className="mt-2 text-sm text-slate-600">
                    Status: {latestWorkflowComplete ? 'Final paper approved' : 'Still in progress'}
                  </p>
                </div>
                <Link to={`/question-bank/${latestSyllabus.id}`}>
                  <Button className="w-full">{latestWorkflowComplete ? 'View Workflow' : 'Open Workflow'}</Button>
                </Link>
              </div>
            ) : (
              <div className="rounded-xl bg-slate-50 p-4 text-sm leading-6 text-slate-600">
                No syllabus has been uploaded yet. Start a new workflow to begin question-bank generation.
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {stats.map(({ label, value, note, icon: Icon }) => (
          <Card key={label} className="rounded-2xl border-slate-200 shadow-sm">
            <CardContent className="flex items-start gap-4 p-5">
              <div className="rounded-xl bg-slate-100 p-3 text-slate-900">
                <Icon size={20} />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-600">{label}</p>
                <p className="mt-1 text-3xl font-bold text-slate-900">{value}</p>
                <p className="mt-1 text-sm text-slate-600">{note}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        {quickActions.map(({ title, description, action, actionLabel }) => (
          <Card key={title} className="rounded-2xl border-slate-200 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-xl">{title}</CardTitle>
              <CardDescription>{description}</CardDescription>
            </CardHeader>
            <CardContent className="pt-0 pb-5">
              <Link to={action}>
                <Button variant="outline" className="w-full justify-between">
                  {actionLabel}
                  <ArrowRight size={16} />
                </Button>
              </Link>
            </CardContent>
          </Card>
        ))}
      </section>

      <section>
        <div className="mb-4">
          <h2 className="text-2xl font-bold text-slate-900">Recent Syllabus Files</h2>
          <p className="mt-1 text-sm text-slate-600">Each syllabus becomes a workflow you can reopen at any time.</p>
        </div>

        {loading ? (
          <div className="py-8 text-center text-slate-500">Loading...</div>
        ) : syllabi.length === 0 ? (
          <Card className="rounded-2xl border-slate-200 shadow-sm">
            <CardContent className="p-10 text-center">
              <FileText className="mx-auto h-12 w-12 text-slate-300" />
              <p className="mt-4 text-lg font-semibold text-slate-900">No syllabus files uploaded yet</p>
              <p className="mt-2 text-sm text-slate-600">Upload a syllabus to create your first teacher workflow.</p>
              <Link to="/upload-syllabus">
                <Button className="mt-5">Upload syllabus</Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {syllabi.map((syllabus) => (
              <Card key={syllabus.id} className="rounded-2xl border-slate-200 shadow-sm">
                <CardHeader>
                  <CardTitle className="text-lg">{syllabus.filename}</CardTitle>
                  <CardDescription>
                    {syllabus.topic_count || 0} units extracted | {formatDate(syllabus.created_at)}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
                    Continue question-bank review, template setup, and final paper generation from this workflow.
                  </div>
                  <Link to={`/question-bank/${syllabus.id}`}>
                    <Button className="w-full">Open Workflow</Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

export default TeacherDashboard

