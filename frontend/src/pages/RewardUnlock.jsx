import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMissionStore } from '../store/missionStore'
import GlitchText from '../components/GlitchText'

const LINES = [
  '> Vérification des credentials…',
  '> Authentification niveau-5 confirmée…',
  '> Déchiffrement du cache…',
  '> Coordonnées de la planque débloquées…',
  '> Accès accordé. Bonne chance, agent.',
]

export default function RewardUnlock() {
  const navigate         = useNavigate()
  const mission          = useMissionStore((s) => s.mission)
  const missionComplete  = useMissionStore((s) => s.missionComplete)
  const remainingSeconds = useMissionStore((s) => s.remainingSeconds)
  const reset            = useMissionStore((s) => s.reset)
  const [visibleLines, setVisibleLines] = useState(0)
  const [showReward, setShowReward]     = useState(false)

  useEffect(() => {
    let i = 0
    const interval = setInterval(() => {
      i++
      setVisibleLines(i)
      if (i >= LINES.length) {
        clearInterval(interval)
        setTimeout(() => setShowReward(true), 400)
      }
    }, 500)
    return () => clearInterval(interval)
  }, [])

  const fmt = (s) => {
    if (s == null) return '--:--'
    const m = Math.floor(s / 60).toString().padStart(2,'0')
    const sec = (s % 60).toString().padStart(2,'0')
    return `${m}:${sec}`
  }

  return (
    <div className="hx-screen flex flex-col p-6 pt-safe">
      {/* Terminal boot sequence */}
      <div className="font-mono text-xs text-hx-teal space-y-1 mb-8 flex-1">
        <div className="text-hx-sub tracking-widest mb-4">// SYSTÈME DE RÉCOMPENSE</div>
        {LINES.slice(0, visibleLines).map((line, i) => (
          <div key={i} className="leading-relaxed">{line}</div>
        ))}
        {visibleLines < LINES.length && (
          <span className="animate-blink">▋</span>
        )}
      </div>

      {/* Bloc principal */}
      {showReward && (
        <div className="space-y-6">
          <div className={`text-center font-mono border-2 p-6 rounded ${
            missionComplete ? 'border-hx-green' : 'border-hx-red'
          }`}>
            <div className={`text-5xl mb-3 ${missionComplete ? 'text-hx-green' : 'text-hx-red'}`}>
              {missionComplete ? '■' : '✕'}
            </div>
            <GlitchText
              text={missionComplete ? 'MISSION ACCOMPLIE' : 'TEMPS ÉCOULÉ'}
              autoPlay
              tag="h2"
              className={`text-xl font-bold ${missionComplete ? 'text-hx-green' : 'text-hx-red'}`}
            />
            {missionComplete && remainingSeconds != null && (
              <div className="text-hx-sub text-xs mt-2">
                Temps restant : {fmt(remainingSeconds)}
              </div>
            )}
          </div>

          {/* Récompense */}
          {mission?.reward_text && missionComplete && (
            <div className="border border-hx-teal bg-hx-surface p-5 rounded font-mono">
              <div className="text-hx-teal text-xs tracking-widest mb-3">// RÉCOMPENSE DÉBLOQUÉE</div>
              <p className="text-hx-text text-sm leading-relaxed font-sans">
                {mission.reward_text}
              </p>
            </div>
          )}

          <button
            onClick={() => { reset(); navigate('/') }}
            className="hx-btn-ghost w-full"
          >
            NOUVELLE MISSION
          </button>
        </div>
      )}
    </div>
  )
}
