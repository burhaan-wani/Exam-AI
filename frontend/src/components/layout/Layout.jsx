import { useMemo, useState } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import {
  BookOpen,
  LayoutDashboard,
  LogOut,
  Menu,
  Upload,
  X,
} from 'lucide-react'
import Button from '../ui/Button'

const Layout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const navigate = useNavigate()
  const location = useLocation()
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  const teacherLinks = [
    {
      path: '/dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      helper: 'Overview and active workflows',
    },
    {
      path: '/upload-syllabus',
      label: 'Start New Workflow',
      icon: Upload,
      helper: 'Upload syllabus and references',
    },
  ]

  const studentLinks = [
    {
      path: '/submit-answers',
      label: 'Submit Answers',
      icon: Upload,
      helper: 'Open the assigned paper',
    },
    {
      path: '/evaluation-results',
      label: 'Results',
      icon: BookOpen,
      helper: 'View evaluated submissions',
    },
  ]

  const navLinks = user.role === 'teacher' ? teacherLinks : studentLinks

  const headerMeta = useMemo(() => {
    if (user.role !== 'teacher') {
      return {
        title: 'Student Portal',
        description: 'View the assigned paper, submit answers, and track evaluation results.',
      }
    }

    if (location.pathname.startsWith('/upload-syllabus')) {
      return {
        title: 'Syllabus Intake',
        description: 'Start the teacher workflow by uploading the syllabus, validating structure, and adding grounding material.',
      }
    }

    if (location.pathname.startsWith('/question-bank/')) {
      return {
        title: 'Question Bank Workflow',
        description: 'Curate the bank, review the blueprint, and move toward a finalized question paper.',
      }
    }

    if (location.pathname.startsWith('/question-paper/')) {
      return {
        title: 'Final Paper Review',
        description: 'Refine the generated paper, approve it, and prepare it for student release.',
      }
    }

    return {
      title: 'Teacher Workspace',
      description: 'Manage the full flow from syllabus upload to final paper approval in one place.',
    }
  }, [location.pathname, user.role])

  return (
    <div className="flex h-screen bg-slate-50 text-gray-900">
      <aside
        className={`${
          sidebarOpen ? 'w-72' : 'w-20'
        } flex shrink-0 flex-col border-r border-slate-200 bg-white transition-all duration-300`}
      >
        <div className="border-b border-slate-200 px-5 py-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-white">
                <LayoutDashboard size={20} />
              </div>
              {sidebarOpen ? (
                <div>
                  <p className="text-lg font-semibold text-slate-900">Exam AI</p>
                  <p className="text-xs text-slate-500">
                    {user.role === 'teacher' ? 'Teacher paper workflow' : 'Student portal'}
                  </p>
                </div>
              ) : null}
            </div>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="rounded-xl p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900"
            >
              {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <nav className="space-y-2">
            {navLinks.map(({ path, label, icon: Icon, helper }) => {
              const isActive = location.pathname === path || location.pathname.startsWith(`${path}/`)
              return (
                <Link
                  key={path}
                  to={path}
                  className={`group flex items-center gap-3 rounded-2xl border px-4 py-3 transition-all ${
                    isActive
                      ? 'border-slate-200 bg-slate-100 text-slate-950'
                      : 'border-transparent text-slate-700 hover:border-slate-200 hover:bg-slate-50 hover:text-slate-950'
                  }`}
                >
                  <div className={`rounded-xl p-2 ${isActive ? 'bg-white text-slate-900' : 'bg-slate-100 text-slate-700'}`}>
                    <Icon size={18} />
                  </div>
                  {sidebarOpen ? (
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold">{label}</p>
                      <p className={`truncate text-xs ${isActive ? 'text-slate-500' : 'text-slate-500'}`}>{helper}</p>
                    </div>
                  ) : null}
                </Link>
              )
            })}
          </nav>
        </div>

        <div className="border-t border-slate-200 p-4">
          {sidebarOpen ? (
            <div className="mb-4 rounded-2xl bg-slate-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Signed in as</p>
              <p className="mt-2 truncate text-sm font-semibold text-slate-900">{user.name}</p>
              <p className="mt-1 text-xs capitalize text-slate-500">{user.role || 'user'}</p>
            </div>
          ) : null}
          <Button
            onClick={handleLogout}
            variant="ghost"
            className="w-full justify-start gap-3 rounded-2xl text-slate-700 hover:bg-slate-100 hover:text-slate-900"
          >
            <LogOut size={18} />
            {sidebarOpen ? 'Logout' : null}
          </Button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="border-b border-slate-200 bg-white px-6 py-5 lg:px-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h2 className="text-3xl font-bold tracking-tight text-slate-900">{headerMeta.title}</h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{headerMeta.description}</p>
            </div>

            {user.role === 'teacher' ? (
              <div className="flex flex-wrap gap-3">
                <Link to="/upload-syllabus">
                  <Button>
                    <Upload size={16} className="mr-2" />
                    New Workflow
                  </Button>
                </Link>
              </div>
            ) : null}
          </div>
        </header>

        <main className="flex-1 overflow-auto px-5 py-5 lg:px-8 lg:py-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout
