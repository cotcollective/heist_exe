/**
 * Une partie — le jeton EST la partie.
 *
 * Rien ici ne demande d'email. On crée une partie, on reçoit un jeton, on le
 * garde dans localStorage, on joue. Le compte n'entre en jeu qu'au moment où
 * l'on veut un point de contrôle durable, et c'est un choix, jamais un péage.
 *
 * Le jeton n'est jamais réaffiché : si on le perd, la partie est perdue. C'est
 * le prix d'une capacité au lieu d'un compte — et c'est ce qui permet de jouer
 * sans formulaire.
 */

const PARTY_KEY = 'hx_party'
const ACCOUNT_KEY = 'hx_account'

function readJSON(key) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : null
  } catch { return null }
}

function writeJSON(key, value) {
  try {
    if (value === null) localStorage.removeItem(key)
    else localStorage.setItem(key, JSON.stringify(value))
  } catch { /* quota plein : la partie reste locale */ }
}

// ── Partie courante ────────────────────────────────────────────────────────

export function currentParty() {
  return readJSON(PARTY_KEY)
}

export function clearParty() {
  writeJSON(PARTY_KEY, null)
}

export function hasParty() {
  const p = currentParty()
  return Boolean(p && p.id && p.token)
}

function saveParty(party, token) {
  writeJSON(PARTY_KEY, { id: party.id, token, kind: party.kind, title: party.title })
  return party
}

// ── Réseau ─────────────────────────────────────────────────────────────────

async function call(path, { method = 'GET', token, body } = {}) {
  const headers = {}
  if (token) headers['X-Party-Token'] = token
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  const res = await fetch(`/api/play${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  })

  if (!res.ok) {
    let detail = `Erreur ${res.status}`
    try { detail = (await res.json()).detail ?? detail } catch { /* corps vide */ }
    throw new Error(detail)
  }
  return res.status === 204 ? null : res.json()
}

/**
 * Démarre une partie. Aucun compte, aucun email, aucun nom.
 * kind = "mission" | "cache"
 */
export async function startParty({ kind = 'mission', refId = null, title = null, state = {} } = {}) {
  const data = await call('/parties', {
    method: 'POST',
    body: { kind, ref_id: refId, title, state },
  })
  return saveParty(data.party, data.token)
}

/**
 * Reprise. Renvoie null si le jeton ne vaut plus rien — auquel cas on repart
 * proprement plutôt que de bloquer le joueur sur une erreur technique.
 */
export async function resumeParty() {
  const p = currentParty()
  if (!p) return null
  try {
    const state = await call(`/parties/${p.id}`, { token: p.token })
    return { ...state, token: p.token }
  } catch {
    clearParty()
    return null
  }
}

/** Point de contrôle. `merge` fusionne au lieu d'écraser. */
export async function checkpoint({ merge, state, title } = {}) {
  const p = currentParty()
  if (!p) return null
  const body = {}
  if (merge !== undefined) body.merge = merge
  if (state !== undefined) body.state = state
  if (title !== undefined) body.title = title
  return call(`/parties/${p.id}`, { method: 'PATCH', token: p.token, body })
}

// ── Compte : conteneur de parties ──────────────────────────────────────────

export function currentAccount() {
  return readJSON(ACCOUNT_KEY)
}

export function hasAccount() {
  const a = currentAccount()
  return Boolean(a && a.id && a.token)
}

/**
 * Crée le conteneur et y rattache la partie courante.
 *
 * L'email est une étiquette, pas une preuve : on n'envoie aucun courrier et
 * on ne prétend rien vérifier. Il sert à retrouver ses parties dans ce
 * navigateur, jamais à les réclamer depuis ailleurs sans le jeton.
 *
 * @returns {{ account, token }} — le jeton de compte n'est montré qu'ici.
 */
export async function createAccountAndAttach(email, label = null) {
  const res = await fetch('/api/play/accounts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, label }),
  })
  if (!res.ok) {
    let detail = `Erreur ${res.status}`
    try { detail = (await res.json()).detail ?? detail } catch { /* vide */ }
    throw new Error(detail)
  }
  const data = await res.json()
  const account = data.account
  const token = data.token

  const p = currentParty()
  if (p) {
    await fetch(`/api/play/accounts/${account.id}/parties`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Account-Token': token },
      body: JSON.stringify({ party_id: p.id, party_token: p.token }),
    })
  }

  writeJSON(ACCOUNT_KEY, { id: account.id, token, email: account.email, label: account.label })
  return { account, token }
}

/** Les parties du conteneur. Vide si aucun compte sur cet appareil. */
export async function listAccountParties() {
  const a = currentAccount()
  if (!a) return []
  const res = await fetch(`/api/play/accounts/${a.id}/parties`, {
    headers: { 'X-Account-Token': a.token },
  })
  if (!res.ok) return []
  return res.json()
}

export function signOutAccount() {
  writeJSON(ACCOUNT_KEY, null)
}
