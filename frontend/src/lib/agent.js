/**
 * Identité d'appareil — paire de clés ECDSA P-256, sans compte.
 *
 * L'appareil génère une paire une seule fois, enregistre la publique sous un
 * nom d'agent, puis signe chaque réclamation. Personne ne peut donc réclamer
 * au nom d'un autre, et il n'y a ni mot de passe ni courriel à gérer.
 *
 * La clé privée ne quitte jamais le navigateur : elle vit dans localStorage.
 * Ce n'est pas un coffre-fort — c'est une identité de jeu de quartier.
 */

const STORAGE_KEY = 'hx_agent_key'

function b64url(buf) {
  const bytes = new Uint8Array(buf)
  let bin = ''
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i])
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

export function subtleAvailable() {
  return typeof crypto !== 'undefined' && !!crypto.subtle
}

async function generateKeypair() {
  const kp = await crypto.subtle.generateKey(
    { name: 'ECDSA', namedCurve: 'P-256' },
    true,
    ['sign', 'verify'],
  )
  const pub = await crypto.subtle.exportKey('jwk', kp.publicKey)
  const priv = await crypto.subtle.exportKey('jwk', kp.privateKey)
  const record = { private_key_jwk: priv, public_jwk: pub }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(record))
  return record
}

async function importPrivate(jwk) {
  return crypto.subtle.importKey(
    'jwk', jwk,
    { name: 'ECDSA', namedCurve: 'P-256' },
    false, ['sign'],
  )
}

/** Charge la paire locale, ou en crée une. */
export async function loadOrCreateKeypair() {
  if (!subtleAvailable()) {
    throw new Error("La signature requiert HTTPS ou localhost (WebCrypto indisponible)")
  }
  const raw = localStorage.getItem(STORAGE_KEY)
  if (raw) {
    try {
      const record = JSON.parse(raw)
      if (record?.private_key_jwk && record?.public_jwk) return record
    } catch { /* corrompu : on régénère */ }
  }
  return generateKeypair()
}

export function publicJwk() {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try { return JSON.parse(raw)?.public_jwk ?? null } catch { return null }
}

/**
 * S'assure que l'appareil est enregistré sous ce nom.
 * Idempotent : même clé + même nom = succès silencieux.
 * 409 si le nom appartient déjà à un autre appareil — c'est volontaire.
 */
export async function ensureAgent(name, registerFn) {
  const record = await loadOrCreateKeypair()
  await registerFn(name.trim(), record.public_jwk)
  return record
}

/** Signe « waypointId|nom|ts » — même forme canonique que le serveur. */
export async function signClaim(waypointId, name, record) {
  const ts = Math.floor(Date.now() / 1000)
  const message = `${waypointId}|${name.trim()}|${ts}`
  const key = await importPrivate(record.private_key_jwk)
  const sig = await crypto.subtle.sign(
    { name: 'ECDSA', hash: 'SHA-256' },
    key,
    new TextEncoder().encode(message),
  )
  return { signature: b64url(sig), ts }
}
