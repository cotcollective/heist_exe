import { useNavigate, useLocation } from 'react-router-dom'
import { useMissionStore } from '../store/missionStore'

export default function HxLayout({ children, showNav = true, title, sub }) {
  return (
    <div className="hx-screen flex flex-col">
      {(title || sub) && (
        <div className="px-4 pt-safe pb-3 border-b border-hx-border shrink-0">
          {sub && <div className="text-hx-sub text-xs tracking-widest mb-1">{sub}</div>}
          {title && <h1 className="text-lg font-bold font-mono text-hx-text">{title}</h1>}
        </div>
      )}
      <div className="flex-1 overflow-y-auto">
        {children}
      </div>
      {showNav && <BottomNav />}
    </div>
  )
}

function BottomNav() {
  const navigate  = useNavigate()
  const location  = useLocation()
  const token     = useMissionStore((s) => s.token)
  const missionComplete = useMissionStore((s) => s.missionComplete)

  const path = location.pathname

  const tabs = [
    { label: 'CARTE',    icon: '◈', to: '/hunt',     active: path === '/hunt' },
    { label: 'BRIEF',    icon: '▤', to: '/briefing', active: path === '/briefing' },
    { label: 'STATUT',   icon: '◉', to: missionComplete ? '/reward' : path, active: path === '/reward' },
  ]

  if (!token) return null

  return (
    <nav className="shrink-0 border-t border-hx-border bg-hx-bg grid grid-cols-3">
      {tabs.map((t) => (
        <button
          key={t.to}
          onClick={() => navigate(t.to)}
          className={`py-3 flex flex-col items-center gap-1 transition-colors ${
            t.active ? 'text-hx-teal' : 'text-hx-dim hover:text-hx-sub'
          }`}
        >
          <span className="text-lg leading-none">{t.icon}</span>
          <span className="text-[9px] tracking-widest font-mono">{t.label}</span>
        </button>
      ))}
    </nav>
  )
}
