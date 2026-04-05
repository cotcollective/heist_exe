import { useNavigate } from 'react-router-dom'
import { useMissionStore } from '../store/missionStore'
import AudioPlayer from '../components/AudioPlayer'
import GlitchText from '../components/GlitchText'
import Countdown from '../components/Countdown'

export default function Briefing() {
  const navigate     = useNavigate()
  const mission      = useMissionStore((s) => s.mission)
  const playerName   = useMissionStore((s) => s.playerName)
  const reset        = useMissionStore((s) => s.reset)

  if (!mission) { navigate('/'); return null }

  const audioSrc = mission.audio_file ? `/media/${mission.audio_file}` : null

  return (
    <div className="hx-screen flex flex-col p-6 pt-safe">
      {/* Header */}
      <div className="mb-6">
        <div className="text-hx-sub text-xs tracking-widest mb-1">// MISSION BRIEFING</div>
        <GlitchText
          text={mission.title.toUpperCase()}
          tag="h1"
          autoPlay
          className="text-2xl font-bold text-hx-text"
        />
        <div className="text-hx-teal text-xs mt-1">
          AGENT: {playerName.toUpperCase()} — {mission.waypoints?.length ?? 0} WAYPOINTS
        </div>
      </div>

      {/* Countdown */}
      <div className="mb-6 border border-hx-border bg-hx-surface p-4 rounded">
        <Countdown onTimeout={() => navigate('/reward')} />
      </div>

      {/* Audio message */}
      {audioSrc && (
        <div className="mb-6">
          <div className="text-hx-sub text-xs tracking-widest mb-2">// TRANSMISSION CHIFFRÉE</div>
          <AudioPlayer src={audioSrc} autoPlay label="MESSAGE DE L'AGENT COORDINATEUR" />
        </div>
      )}

      {/* Lore */}
      {mission.lore && (
        <div className="mb-6 flex-1 border-l-2 border-hx-teal pl-4">
          <div className="text-hx-sub text-xs tracking-widest mb-2">// CONTEXTE OPÉRATIONNEL</div>
          <p className="text-hx-text text-sm leading-relaxed font-sans">{mission.lore}</p>
        </div>
      )}

      {/* Actions */}
      <div className="mt-auto flex gap-3">
        <button
          onClick={() => { reset(); navigate('/') }}
          className="hx-btn-ghost"
        >
          ABORT
        </button>
        <button
          onClick={() => navigate('/hunt')}
          className="hx-btn-primary flex-1"
        >
          DÉMARRER LA MISSION ▶
        </button>
      </div>
    </div>
  )
}
