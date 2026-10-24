/**
 * Le point de contrôle, proposé — jamais imposé.
 *
 * Il apparaît aux moments où la partie vaut quelque chose : mission terminée,
 * jalon franchi, cache trouvée. Il propose de garder l'avancement ; il ne
 * demande rien pour continuer à jouer.
 *
 * L'email n'est pas vérifié et ne prétend pas l'être. Ce qui protège la
 * partie, c'est le jeton — l'email ne sert qu'à s'y retrouver.
 */

import { useState } from 'react'
import { createAccountAndAttach, hasAccount, currentAccount } from '../lib/party'

export default function Checkpoint({ partyTitle, onDone }) {
  const [open, setOpen] = useState(false)
  const [email, setEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(false)

  if (hasAccount() && !saved) {
    const a = currentAccount()
    return (
      <div className="text-xs font-mono text-hx-dim">
        Partie liée à <span className="text-hx-green">{a.email}</span>
      </div>
    )
  }

  if (saved) {
    return (
      <div className="text-xs font-mono text-hx-green">
        ✓ Partie enregistrée. Elle te suivra sur cet appareil.
      </div>
    )
  }

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await createAccountAndAttach(email.trim(), partyTitle)
      setSaved(true)
      onDone?.()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (!open) {
    return (
      <div className="mt-4">
        <button
          onClick={() => setOpen(true)}
          className="text-xs font-mono text-hx-dim underline hover:text-hx-green"
        >
          Garder cette partie
        </button>
        <div className="text-[10px] text-hx-dim mt-1">
          Facultatif — sans ça, elle reste dans ce navigateur et disparaît si tu le vides.
        </div>
      </div>
    )
  }

  return (
    <form onSubmit={submit} className="mt-4 border border-hx-line p-3">
      <div className="text-xs font-mono text-hx-dim mb-2">
        Un email pour retrouver tes parties. Pas de mot de passe, pas de
        confirmation — c'est une étiquette, pas un compte sécurisé.
      </div>
      <div className="flex gap-2">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="toi@exemple.com"
          className="flex-1 bg-black border border-hx-line px-2 py-1 text-sm font-mono"
        />
        <button
          type="submit"
          disabled={busy}
          className="border border-hx-green text-hx-green px-3 py-1 text-xs font-mono disabled:opacity-40"
        >
          {busy ? '…' : 'GARDER'}
        </button>
      </div>
      {error && <div className="text-xs text-hx-red mt-2">{error}</div>}
      <button
        type="button"
        onClick={() => setOpen(false)}
        className="text-[10px] text-hx-dim mt-2 underline"
      >
        plus tard
      </button>
    </form>
  )
}
