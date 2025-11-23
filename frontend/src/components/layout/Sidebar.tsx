import { Home, Library, LogOut, User } from "lucide-react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { cn } from "../../lib/utils"
import { useAuthStore } from "../../store/authStore"
import logoImg from "../../assets/logo.png"

const navigation = [
  { name: "Dashboard", href: "/", icon: Home },
  { name: "Biblioteca", href: "/library", icon: Library },
]

export function Sidebar() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-full w-64 flex-col border-r border-slate-200 bg-gradient-to-b from-white to-slate-50">
      {/* Logo section with modern gradient */}
      <div className="flex h-16 items-center px-6 border-b border-slate-200">
        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-600 to-teal-600 shadow-md p-1.5">
          <img src={logoImg} alt="CortAI Logo" className="w-full h-full object-contain" />
        </div>
        <div className="ml-3">
          <span className="text-xl font-bold text-slate-900">
            CortAI
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                "group flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                isActive
                  ? "bg-gradient-to-r from-indigo-50 to-teal-50 text-indigo-700 shadow-sm"
                  : "text-slate-700 hover:bg-slate-100 hover:text-slate-900"
              )}
            >
              <item.icon
                className={cn(
                  "mr-3 h-5 w-5 flex-shrink-0 transition-colors",
                  isActive ? "text-indigo-600" : "text-slate-400 group-hover:text-slate-600"
                )}
                strokeWidth={2}
              />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* User info and logout */}
      <div className="border-t border-slate-200 p-4 bg-white/50">
        <div className="flex items-center mb-3 p-2 rounded-lg hover:bg-slate-50 transition-colors">
          <div className="relative">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-teal-500 shadow-md">
              <User className="h-5 w-5 text-white" strokeWidth={2} />
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 border-2 border-white rounded-full" />
          </div>
          <div className="ml-3 flex-1 min-w-0">
            <p className="text-sm font-semibold text-slate-900 truncate">
              {user?.name || 'Usuário'}
            </p>
            <p className="text-xs text-slate-500 truncate">
              {user?.email || ''}
            </p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center px-3 py-2 text-sm font-medium text-red-600 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 hover:border-red-300 transition-all"
        >
          <LogOut className="h-4 w-4 mr-2" strokeWidth={2} />
          Sair
        </button>
      </div>
    </div>
  )
}

