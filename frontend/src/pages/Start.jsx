/**
 * Création d'une partie — le point d'entrée sans formulaire.
 *
 * On choisit : une mission, ou le monde (chasse libre). Un jeton est généré
 * à la volée et rangé dans le navigateur. Pas de nom, pas d'email, pas de
 * code. Si une partie est déjà en cours, on propose de la reprendre.
 */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import {
  currentParty, hasParty, clearParty, startParty, resumeParty,
} from '../lib/party'
import GlitchText from '../components/GlitchText'

export default function Start() {
  const navigate = useNavigate()

  const [missions, setMissions] = useState([])
  const [resumable, setResumable] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.listActive().then(setMissions).catch(() => {})
    if (hasParty()) {
      const p = currentParty()
      resumeParty()
        .then((state) => {
          if (state) setResumable(state)
          else setResumable(null)
        })
        .catch(() => setResumable(null))
      // On garde les métadonnées locales même si le serveur ne répond pas.
      if (!resumable) setResumable({ ...p, offline: true })
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  async function begin({ kind, refId = null, title = null, to }) {
    setBusy(true)
    setError(null)
    try {
      await startParty({ kind, refId, title })
      navigate(to)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="hx-screen flex flex-col p-6 pt-safe">
      <div className="mb-6">
        <div className="text-hx-sub text-xs tracking-widest mb-2">// NOUVELLE PARTIE</div>
        <GlitchText text="COMMENCER" tag="h1" autoPlay
                    className="text-4xl font-bold text-hx-text" />
        <div className="text-hx-teal text-xs mt-2 tracking-widest">
          aucun compte — rien à remplir
        </div>
      </div>

      {resumable && (
        <div className="border border-hx-green/40 bg-hx-green/5 p-4 mb-6 font-mono">
          <div className="text-hx-green text-xs tracking-widest mb-1">PARTIE EN COURS</div>
          <div className="text-hx-text text-sm">{resumable.title || 'Sans titre'}</div>
          <div className="flex gap-2 mt-3">
            <button
              onClick={() => navigate(resumable.kind === 'cache' ? '/world' : '/briefing')}
              className="border border-hx-green text-hx-green px-3 py-1 text-xs"
            >
              REPRENDRE ▶
            </button>
            <button
              onClick={() => { clearParty(); setResumable(null) }}
              className="text-hx-dim text-xs underline"
            >
              oublier
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="text-hx-red text-xs font-mono border border-hx-red/30 p-3 mb-4">
          // {error}
        </div>
      )}

      <div className="flex-1 flex flex-col justify-center space-y-5 py-2">
        <div>
          <div className="text-hx-sub text-xs tracking-widest mb-2">// UNE MISSION</div>
          <div className="space-y-2">
            {missions.length === 0 && (
              <div className="text-hx-dim text-xs font-mono">
                Aucune mission active pour l&apos;instant.
              </div>
            )}
            {missions.map((m) => (
              <button
                key={m.id}
                disabled={busy}
                onClick={() => begin({
                  kind: 'mission',
                  refId: m.id,
                  title: m.title,
                  to: '/briefing',
                })}
                className="w-full text-left border border-hx-border bg-hx-surface p-4 font-mono hover:border-hx-teal transition-colors disabled:opacity-40"
              >
                <div className="text-hx-teal text-xs tracking-widest mb-1">
                  MISSION_{String(m.id).padStart(3, '0')}
                </div>
                <div className="text-hx-text text-sm font-semibold">{m.title}</div>
                <div className="text-hx-sub text-xs mt-1">
                  {m.duration_minutes} min // {m.waypoints?.length ?? 0} étapes
                </div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <div className="text-hx-sub text-xs tracking-widest mb-2">// OU LE MONDE</div>
          <button
            disabled={busy}
            onClick={() => begin({ kind: 'cache', title: 'Chasse libre', to: '/world' })}
            className="w-full text-left border border-hx-border bg-hx-surface p-4 font-mono hover:border-hx-green transition-colors disabled:opacity-40"
          >
            <div className="text-hx-green text-xs tracking-widest mb-1">CHASSE LIBRE</div>
            <div className="text-hx-text text-sm font-semibold">Chercher les caches cachées</div>
            <div className="text-hx-sub text-xs mt-1">
              aucune mission, aucune étape — juste le quartier
            </div>
          </button>
        </div>
      </div>

      <div className="pt-6 text-center">
        <button onClick={() => navigate('/')}
                className="text-hx-dim text-xs font-mono hover:text-hx-sub">
          ← retour
        </button>
      </div>
    </div>
  )
}
