/**
 * Base de l'API.
 *
 * En développement et en mono-port, le frontend et l'API partagent l'origine :
 * base vide, chemins relatifs. Quand le frontend est servi ailleurs (CDN
 * statique, Surge), il faut pointer l'API explicitement au build :
 *
 *   VITE_API_BASE=https://chasse.exemple.store npm run build
 *
 * Ce n'est pas une variable de runtime : Vite l'inline au build. Un build
 * statique ne peut pas changer d'API sans être reconstruit — c'est le prix
 * du CDN, et c'est acceptable parce que le backend ne bouge pas.
 */
export const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

/** Construit une URL d'API. `path` commence par « / ». */
export function apiUrl(path) {
  return `${API_BASE}/api${path}`
}
