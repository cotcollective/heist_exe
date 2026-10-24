/**
 * File de versement — pour que « verser au monde » survive à une coupure.
 *
 * L'endpoint /world/publish est idempotent sur (mission_id, waypoint_id) :
 * rejouer un lot ne crée pas de doublon, il renvoie les caches existantes
 * avec created=false. C'est ce qui rend une file de retry sûre — on peut
 * renvoyer sans réfléchir.
 *
 * Politique de sortie de file :
 *   - succès                → l'entrée sort
 *   - 4xx (sauf 408/429)    → échec définitif, l'entrée sort et on le signale
 *   - réseau / 5xx / timeout → l'entrée reste, on réessaiera
 *
 * On s'arrête au premier échec réseau : inutile de marteler un serveur
 * injoignable avec quinze lots.
 */

const KEY = 'hx_publish_outbox'

function read() {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? JSON.parse(raw) : []
  } catch { return [] }
}

function write(entries) {
  try { localStorage.setItem(KEY, JSON.stringify(entries)) } catch { /* quota */ }
}

export function outboxSize() {
  return read().length
}

export function outboxEntries() {
  return read()
}

export function enqueue(items) {
  const entries = read()
  const id = (globalThis.crypto?.randomUUID?.() ?? `q_${Date.now()}_${Math.random()}`)
  entries.push({ id, items, at: Date.now(), attempts: 0 })
  write(entries)
  return id
}

export function clearOutbox() {
  write([])
}

/**
 * Tente de vider la file.
 * @param publishFn  (items) => Promise<resultat>
 * @returns { sent, dropped, remaining, lastError }
 */
export async function flush(publishFn) {
  let entries = read()
  if (entries.length === 0) return { sent: 0, dropped: 0, remaining: 0 }

  let sent = 0
  let dropped = 0
  let lastError = null
  const kept = []

  for (let i = 0; i < entries.length; i++) {
    const entry = entries[i]
    try {
      await publishFn(entry.items)
      sent++
    } catch (e) {
      const msg = String(e?.message ?? e)
      const transient = /réseau|network|fetch|timeout|502|503|504|Failed to fetch|Load failed/i.test(msg)

      if (transient) {
        // On garde celle-ci ET tout le reste, sans réessayer en rafale.
        lastError = msg
        kept.push({ ...entry, attempts: (entry.attempts ?? 0) + 1 })
        kept.push(...entries.slice(i + 1))
        break
      }

      // Échec définitif (400, 403, 409…) : inutile de réessayer à l'infini.
      dropped++
      lastError = msg
    }
  }

  write(kept)
  return { sent, dropped, remaining: kept.length, lastError }
}
