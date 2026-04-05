import { useEffect, useRef } from 'react'
import { useMissionStore } from '../store/missionStore'
import { createCountdownSocket } from '../api/client'

function fmt(s) {
  const m = Math.floor(s / 60).toString().padStart(2, '0')
  const sec = (s % 60).toString().padStart(2, '0')
  return `${m}:${sec}`
}

export default function Countdown({ onTimeout }) {
  const { mission, sessionId, remainingSeconds, tickTimer } = useMissionStore()
  const wsRef = useRef(null)
  const intervalRef = useRef(null)

  useEffect(() => {
    if (!mission || !sessionId) return

    // Fallback local si WS échoue
    const startLocalTimer = () => {
      intervalRef.current = setInterval(() => {
        tickTimer()
      }, 1000)
    }

    wsRef.current = createCountdownSocket(
      mission.id,
      sessionId,
      (remainingSeconds ?? mission.duration_minutes * 60),
      {
        onTick: (secs) => useMissionStore.setState({ remainingSeconds: secs }),
        onTimeout: () => onTimeout?.(),
        onError: startLocalTimer,
      }
    )

    return () => {
      wsRef.current?.close()
      clearInterval(intervalRef.current)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const secs = remainingSeconds ?? (mission?.duration_minutes ?? 45) * 60
  const pct = mission ? (secs / (mission.duration_minutes * 60)) * 100 : 100
  const isCritical = secs < 120
  const isWarning  = secs < 300

  return (
    <div className={`font-mono text-center ${isCritical ? 'animate-countdown-warn' : ''}`}>
      <div className={`text-xs tracking-widest mb-1 ${
        isCritical ? 'text-hx-red' : isWarning ? 'text-hx-amber' : 'text-hx-sub'
      }`}>
        {isCritical ? '// SIGNAL TRACÉ — ÉVACUEZ' : isWarning ? '// TEMPS CRITIQUE' : '// TEMPS RESTANT'}
      </div>
      <div className={`text-4xl font-bold tabular-nums ${
        isCritical ? 'text-hx-red' : isWarning ? 'text-hx-amber' : 'text-hx-teal'
      }`}>
        {fmt(secs)}
      </div>
      {/* Barre de progression */}
      <div className="mt-2 h-1 bg-hx-muted rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-1000 rounded-full ${
            isCritical ? 'bg-hx-red' : isWarning ? 'bg-hx-amber' : 'bg-hx-teal'
          }`}
          style={{ width: `${Math.max(0, pct)}%` }}
        />
      </div>
    </div>
  )
}
