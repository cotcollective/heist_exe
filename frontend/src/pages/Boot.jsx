import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useMissionStore } from '../store/missionStore'
import GlitchText from '../components/GlitchText'

export default function Boot() {
  const navigate = useNavigate()
  const setAuth = useMissionStore((s) => s.setAuth)
  const token = useMissionStore((s) => s.token)

  const [missions, setMissions] = useState([])
  const [selected, setSelected] = useState(null)
  const [pin, setPin] = useState('')
  const [playerName, setPlayerName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [booting, setBooting] = useState(true)

  useEffect(() => {
    if (token) { navigate('/briefing'); return }
    const t = setTimeout(() => {
      setBooting(false)
      api.listActive().then(setMissions).catch(() => { })
    }, 1200)
    return () => clearTimeout(t)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleAuth = async (e) => {
    e.preventDefault()
    if (!selected || !pin) return
    setError('')
    setLoading(true)
    try {
      const res = await api.auth(selected.id, pin, playerName || 'Agent')
      setAuth(res.access_token, res.mission, null, playerName || 'Agent')
      navigate('/briefing')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (booting) return (
    <div className="hx-screen flex items-center justify-center">
      <div className="font-mono text-center">
        <div className="text-hx-teal text-xs tracking-[0.3em] mb-4">INITIALISATION SYSTÈME</div>
        <div className="text-hx-dim text-xs animate-blink">▋</div>
      </div>
    </div>
  )

  return (
    <div className="hx-screen flex flex-col p-6 pt-safe">
      {/* Header */}
      <div className="mb-8">
        <div className="text-hx-sub text-xs tracking-widest mb-2">// URBAN MISSION PLATFORM</div>
        <GlitchText
          text="HEIST.EXE"
          tag="h1"
          autoPlay
          className="text-5xl font-bold text-hx-text"
        />
        <div className="text-hx-teal text-xs mt-2 tracking-widest">v0.1.0 — TÉTREAULTVILLE DISTRICT</div>
      </div>

      {/* Sélection mission */}
      {missions.length > 0 && !selected && (
        <div className="flex-1">
          <div className="text-hx-sub text-xs tracking-widest mb-3">// MISSIONS ACTIVES</div>
          <div className="space-y-2">
            {missions.map((m) => (
              <button
                key={m.id}
                onClick={() => setSelected(m)}
                data-testid={`mission-card-${m.id}`}
                className="w-full text-left border border-hx-border bg-hx-surface p-4 rounded hover:border-hx-teal transition-colors font-mono"
              >
                <div className="text-hx-teal text-xs tracking-widest mb-1">
                  MISSION_{String(m.id).padStart(3, '0')}
                </div>
                <div className="text-hx-text text-sm font-semibold">{m.title}</div>
                <div className="text-hx-sub text-xs mt-1">{m.duration_minutes} min // {m.waypoints?.length ?? 0} waypoints</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Formulaire auth */}
      {selected && (
        <form onSubmit={handleAuth} className="flex-1 flex flex-col gap-4">
          <div>
            <div className="text-hx-sub text-xs tracking-widest mb-2">// MISSION SÉLECTIONNÉE</div>
            <div className="border border-hx-teal bg-hx-surface p-3 rounded font-mono">
              <div className="text-hx-teal text-xs tracking-widest mb-1">MISSION_{String(selected.id).padStart(3, '0')}</div>
              <div className="text-hx-text text-sm">{selected.title}</div>
            </div>
          </div>

          <div className="hx-field">
            <label className="hx-label">NOM D'AGENT</label>
            <input
              type="text"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              placeholder="ex: Agent_X"
              data-testid="player-name"
              className="hx-input"
              maxLength={30}
            />
          </div>

          <div className="hx-field">
            <label className="hx-label">CODE D'ACCÈS (PIN)</label>
            <input
              type="password"
              inputMode="numeric"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              placeholder="••••"
              data-testid="pin-input"
              className="hx-input text-center text-2xl tracking-[0.5em]"
              maxLength={10}
              required
            />
          </div>

          {error && (
            <div className="text-hx-red text-xs font-mono border border-hx-red/30 bg-hx-red/5 p-3 rounded">
              // ACCÈS REFUSÉ — {error}
            </div>
          )}

          <div className="mt-auto flex gap-3">
            <button type="button" onClick={() => setSelected(null)} className="hx-btn-ghost flex-1">
              ← RETOUR
            </button>
            <button type="submit" data-testid="submit-auth" disabled={loading} className="hx-btn-primary flex-2">
              {loading ? 'VÉRIFICATION…' : 'ENTRER ▶'}
            </button>
          </div>
        </form>
      )}

      {missions.length === 0 && !selected && (
        <div className="flex-1 flex items-center justify-center">
          <div className="font-mono text-center text-hx-sub text-sm">
            <div className="text-3xl mb-4">⊘</div>
            Aucune mission active.<br />
            <span className="text-xs text-hx-dim">Attends le signal de l&apos;agent coordinateur.</span>
            <div className="mt-6">
              <button
                onClick={() => navigate('/admin')}
                className="text-hx-teal text-xs tracking-widest font-mono border border-hx-teal/30 px-4 py-2 rounded hover:bg-hx-teal/5 transition-colors"
              >
                🛡️ ACCÈS COORDINATEUR (PAPA)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer discret — Papa peut toujours accéder à l'admin */}
      {!selected && (
        <div className="pt-4 pb-2 text-center">
          <button
            onClick={() => navigate('/admin')}
            className="text-hx-dim text-xs font-mono hover:text-hx-sub transition-colors"
          >
            // accès coordinateur
          </button>
        </div>
      )}
    </div>
  )
}
