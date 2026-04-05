import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { adminApi } from '../../api/client'
import { useAdminKey } from '../../hooks/useAdminKey'
import GlitchText from '../../components/GlitchText'
import { HxButton, HxCard, HxBadge } from '../../components/HxAtoms'

export default function AdminDashboard() {
  const navigate = useNavigate()
  const adminKey = useAdminKey()
  const [missions, setMissions] = useState([])
  const [loading, setLoading]   = useState(true)
  const [deleting, setDeleting] = useState(null)

  const load = async () => {
    if (!adminKey) return
    try {
      const data = await adminApi.listMissions(adminKey)
      setMissions(data)
    } catch {
      navigate('/admin')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [adminKey]) // eslint-disable-line

  const handleDelete = async (id, title) => {
    if (!window.confirm(`Supprimer "${title}" ? Action irréversible.`)) return
    setDeleting(id)
    try {
      await adminApi.deleteMission(adminKey, id)
      setMissions((prev) => prev.filter((m) => m.id !== id))
    } finally {
      setDeleting(null)
    }
  }

  const logout = () => { sessionStorage.removeItem('hx_admin_key'); navigate('/admin') }

  return (
    <div className="hx-screen flex flex-col">
      <div className="px-4 pt-safe pb-3 border-b border-hx-border flex items-start justify-between shrink-0">
        <div>
          <div className="text-hx-amber text-xs tracking-widest mb-1">// COORDINATEUR</div>
          <GlitchText text="MISSIONS" tag="h1" autoPlay className="text-2xl font-bold text-hx-text" />
        </div>
        <button onClick={logout}
          className="text-hx-dim text-xs font-mono hover:text-hx-red transition-colors mt-1">
          LOGOUT
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {loading && (
          <div className="text-hx-sub text-xs font-mono text-center py-8 animate-blink">
            Chargement…
          </div>
        )}

        {!loading && missions.length === 0 && (
          <div className="text-center py-12">
            <div className="text-4xl mb-3 text-hx-dim">⊘</div>
            <div className="text-hx-sub text-sm font-mono">Aucune mission créée.</div>
            <div className="text-hx-dim text-xs mt-1">Crée ta première mission ci-dessous.</div>
          </div>
        )}

        {missions.map((m) => (
          <HxCard key={m.id}>
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex-1 min-w-0">
                <div className="text-hx-amber text-[10px] tracking-widest font-mono mb-1">
                  MISSION_{String(m.id).padStart(3, '0')}
                </div>
                <div className="text-hx-text text-sm font-bold font-mono truncate">{m.title}</div>
              </div>
              <HxBadge variant={m.is_active ? 'teal' : 'default'}>
                {m.is_active ? 'ACTIVE' : 'OFF'}
              </HxBadge>
            </div>

            <div className="flex gap-3 text-xs text-hx-dim font-mono mb-3">
              <span>⏱ {m.duration_minutes}min</span>
              <span>◈ {m.waypoints?.length ?? 0} waypoints</span>
              {m.audio_file && <span>♫ audio</span>}
            </div>

            <div className="flex gap-2">
              <HxButton variant="ghost" className="flex-1 text-xs py-1.5"
                onClick={() => navigate(`/admin/builder/${m.id}`)}>
                ÉDITER
              </HxButton>
              <HxButton variant="danger" className="text-xs py-1.5 px-3"
                loading={deleting === m.id}
                onClick={() => handleDelete(m.id, m.title)}>
                ✕
              </HxButton>
            </div>
          </HxCard>
        ))}
      </div>

      <div className="px-4 py-4 border-t border-hx-border shrink-0">
        <HxButton className="w-full py-3" onClick={() => navigate('/admin/builder/new')}>
          + NOUVELLE MISSION
        </HxButton>
      </div>
    </div>
  )
}
