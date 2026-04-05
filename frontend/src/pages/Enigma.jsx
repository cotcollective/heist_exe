import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useMissionStore } from '../store/missionStore'
import Countdown from '../components/Countdown'
import GlitchText from '../components/GlitchText'
import QRScanner from '../components/QRScanner'

export default function Enigma() {
  const { waypointId }    = useParams()
  const navigate          = useNavigate()
  const token             = useMissionStore((s) => s.token)
  const currentWaypoint   = useMissionStore((s) => s.currentWaypoint)
  const advanceToWaypoint = useMissionStore((s) => s.advanceToWaypoint)
  const setMissionComplete= useMissionStore((s) => s.setMissionComplete)

  const [answer, setAnswer]   = useState('')
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState(null)  // null | 'wrong' | 'correct'
  const [showQR, setShowQR]   = useState(false)

  const wp = currentWaypoint

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!answer.trim()) return
    setError('')
    setLoading(true)
    try {
      const res = await api.submitAnswer(parseInt(waypointId), answer, token)
      if (!res.correct) {
        setResult('wrong')
        setError('Code incorrect — réessaie.')
        setLoading(false)
        return
      }
      setResult('correct')
      if (res.mission_complete) {
        setMissionComplete()
        setTimeout(() => navigate('/reward'), 1200)
      } else {
        advanceToWaypoint(res.next_waypoint)
        setTimeout(() => navigate('/hunt'), 1200)
      }
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  if (!wp) { navigate('/hunt'); return null }

  // ── Écran succès ────────────────────────────────────────────────────────────
  if (result === 'correct') {
    return (
      <div className="hx-screen flex flex-col p-6 pt-safe">
        <div className="mb-6"><Countdown onTimeout={() => navigate('/reward')} /></div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center font-mono">
            <div className="text-6xl mb-4 text-hx-green">✓</div>
            <GlitchText text="ACCÈS ACCORDÉ" autoPlay className="text-2xl font-bold text-hx-green" />
            <div className="text-hx-sub text-xs mt-3 animate-blink">
              Chargement du prochain waypoint…
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="hx-screen flex flex-col p-6 pt-safe">
      {/* Header */}
      <div className="mb-6">
        <div className="text-hx-sub text-xs tracking-widest mb-1">
          // ÉNIGME — {wp.title.toUpperCase()}
        </div>
        <Countdown onTimeout={() => navigate('/reward')} />
      </div>

      {/* Question */}
      <div className="mb-5 border-l-2 border-hx-teal pl-4">
        <div className="text-hx-sub text-xs tracking-widest mb-2">// QUESTION</div>
        <p className="text-hx-text text-sm leading-relaxed font-sans">
          {wp.enigma?.question ?? 'Aucune énigme pour ce waypoint.'}
        </p>
        {wp.enigma?.hint && (
          <p className="text-hx-dim text-xs mt-2 italic font-sans">{wp.enigma.hint}</p>
        )}
      </div>

      {/* QR Scanner — nouveau composant standalone */}
      {wp.qr_code && !showQR && (
        <button
          onClick={() => setShowQR(true)}
          className="hx-btn-ghost w-full text-xs mb-4"
        >
          ◉ SCANNER QR CODE
        </button>
      )}
      {showQR && (
        <div className="mb-4">
          <QRScanner
            label="SCANNER LE QR DU WAYPOINT"
            onResult={(decoded) => {
              setAnswer(decoded)
              setShowQR(false)
            }}
            onClose={() => setShowQR(false)}
          />
        </div>
      )}

      {/* Input réponse */}
      <form onSubmit={handleSubmit} className="flex flex-col gap-4 flex-1">
        <div className="hx-field">
          <label className="hx-label">CODE DE PASSE</label>
          <input
            type="text"
            value={answer}
            onChange={(e) => { setAnswer(e.target.value); setError(''); setResult(null) }}
            placeholder="Entrer la réponse…"
            className={`hx-input ${result === 'wrong' ? 'border-hx-red' : ''}`}
            autoComplete="off"
            autoCapitalize="off"
            autoCorrect="off"
          />
        </div>

        {error && (
          <div className="text-hx-red text-xs font-mono border border-hx-red/30 bg-hx-red/5 p-3 rounded">
            // {error}
          </div>
        )}

        <div className="mt-auto flex gap-3">
          <button type="button" onClick={() => navigate('/hunt')} className="hx-btn-ghost">
            ← CARTE
          </button>
          <button
            type="submit"
            disabled={loading || !answer.trim()}
            className="hx-btn-primary flex-1"
          >
            {loading ? 'VALIDATION…' : 'SOUMETTRE ▶'}
          </button>
        </div>
      </form>
    </div>
  )
}
