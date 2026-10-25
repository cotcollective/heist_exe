/**
 * Countdown — l'horloge de la mission.
 *
 * Elle se calcule sur le TEMPS MURAL depuis `startedAt`, pas sur un compteur
 * qu'on décrémente. Trois défauts réels l'ont imposé :
 *
 * 1. Elle ne dépend plus du WebSocket. Avant, une garde `if (!sessionId)`
 *    sortait de l'effet — et `sessionId` valait null (Boot passait `null`).
 *    Donc aucun tick, aucun repli local, un 45:00 figé pour toujours. Une
 *    horloge qui s'arrête quand un socket manque n'est pas une horloge.
 *
 * 2. Elle ne dérive pas. `setInterval` est étranglé quand l'onglet passe en
 *    arrière-plan (souvent une fois par minute). Un compteur décrémenté perd
 *    alors tout le temps non compté. Ici on recalcule depuis l'heure : un
 *    tick en retard n'enlève rien.
 *
 * 3. Elle survit au rechargement. `startedAt` est persisté, donc reprendre
 *    la partie reprend le vrai temps écoulé.
 *
 * Le WebSocket du serveur, lui, repartait à `duration` à chaque connexion :
 * une coupure réseau redonnait le temps plein. Un enfant qui perd le réseau
 * dans l'escalier aurait gagné du temps. On ne s'en sert plus pour l'affichage.
 */

import { useEffect, useRef, useState } from 'react'
import { useMissionStore } from '../store/missionStore'

function fmt(s) {
  const m = Math.floor(s / 60).toString().padStart(2, '0')
  const sec = Math.floor(s % 60).toString().padStart(2, '0')
  return `${m}:${sec}`
}

export default function Countdown({ onTimeout }) {
  const mission = useMissionStore((s) => s.mission)
  const startedAt = useMissionStore((s) => s.startedAt)
  const setRemaining = useMissionStore((s) => s.setRemaining)

  const total = (mission?.duration_minutes ?? 45) * 60

  // Origine : le début enregistré. Fixée une fois pour ne pas glisser à
  // chaque rendu.
  const t0Ref = useRef(startedAt ?? Date.now())

  // Le tick ne sert qu'à redessiner ; la valeur vient de l'heure.
  const [, force] = useState(0)
  const firedRef = useRef(false)

  useEffect(() => {
    const id = setInterval(() => force((n) => n + 1), 1000)
    return () => clearInterval(id)
  }, [])

  const elapsed = Math.floor((Date.now() - t0Ref.current) / 1000)
  const secs = Math.max(0, total - elapsed)

  useEffect(() => {
    setRemaining?.(secs)
    if (secs === 0 && !firedRef.current) {
      firedRef.current = true
      onTimeout?.()
    }
  }, [secs]) // eslint-disable-line react-hooks/exhaustive-deps

  const pct = total > 0 ? (secs / total) * 100 : 100
  const isCritical = secs < 120
  const isWarning = secs < 300

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
