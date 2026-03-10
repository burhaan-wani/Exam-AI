import { useState } from 'react'
import { Outlet, Link, useNavigate } from 'react-router-dom'
import { Menu, X, LogOut, LayoutDashboard, Upload, BookOpen } from 'lucide-react'
import Button from '../ui/Button'

const Layout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const navigate = useNavigate()
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  const teacherLinks = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/upload-syllabus', label: 'Upload Syllabus', icon: Upload },
  ]

  const studentLinks = [
    { path: '/submit-answers', label: 'Submit Answers', icon: Upload },
    { path: '/evaluation-results', label: 'Results', icon: BookOpen },
  ]

  const navLinks = user.role === 'teacher' ? teacherLinks : studentLinks

  return (
    <div className="flex h-screen bg-gray-50">
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-20'
        } bg-slate-900 text-white transition-all duration-300 border-r border-slate-800`}
      >
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          {sidebarOpen && <h1 className="text-xl font-bold">Exam AI</h1>}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          {navLinks.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <Icon size={20} />
              {sidebarOpen && <span className="text-sm font-medium">{label}</span>}
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-800 space-y-3">
          {sidebarOpen && user.role === 'teacher' && (
            <div className="rounded-lg bg-slate-800 p-3 text-xs text-slate-300">
              <p className="font-semibold text-white">New teacher workflow</p>
              <p className="mt-1">Upload syllabus, generate the question bank, then build and refine the paper.</p>
            </div>
          )}
          {sidebarOpen && (
            <div className="text-xs">
              <p className="text-gray-400">Logged in as</p>
              <p className="font-semibold truncate">{user.name}</p>
            </div>
          )}
          <Button
            onClick={handleLogout}
            variant="ghost"
            className="w-full justify-start gap-3 text-red-400 hover:text-red-300 hover:bg-slate-800"
          >
            <LogOut size={20} />
            {sidebarOpen && 'Logout'}
          </Button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white border-b border-gray-200 px-8 py-4 shadow-sm">
          <h2 className="text-2xl font-bold text-gray-800">
            {user.role === 'teacher' ? 'Teacher Workspace' : 'Student Portal'}
          </h2>
        </header>

        <main className="flex-1 overflow-auto p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout
