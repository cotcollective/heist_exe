/**
 * Tuiles raster : calcul de couverture et estimation.
 *
 * Contrainte assumée : la politique d'usage des tuiles OSM interdit le
 * téléchargement massif (ordre de grandeur : pas plus d'une zone de ~250
 * tuiles à partir du zoom 13). On plafonne donc chaque téléchargement, et
 * l'UI l'affiche. Pour de plus grandes zones il faudra une source tuilée
 * dédiée (PMTiles auto-hébergé), pas les tuiles publiques d'OSM.
 */

export const TILE_CACHE = 'osm-tiles'

// Un seul hôte, sans sous-domaine {s} : la clé de cache doit être
// exactement l'URL demandée par la carte, sinon le prefetch ne sert à rien.
export const TILE_URL = (z, x, y) => `https://tile.openstreetmap.org/${z}/${x}/${y}.png`

// Budget par téléchargement. Volontairement bas : politique OSM.
export const TILE_BUDGET = 250

// ~12 Ko par tuile PNG en moyenne à ces zooms.
export const BYTES_PER_TILE = 12 * 1024

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v))
}

export function lngLatToTile(lng, lat, z) {
  const n = 2 ** z
  const x = Math.floor(((lng + 180) / 360) * n)
  const latRad = (lat * Math.PI) / 180
  const y = Math.floor(
    ((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) * n
  )
  return { x: clamp(x, 0, n - 1), y: clamp(y, 0, n - 1) }
}

/** Étend une liste de points d'une marge en degrés, puis renvoie les bornes. */
export function boundsFromPoints(points, padMeters = 400) {
  if (!points?.length) return null
  const lats = points.map((p) => p.lat)
  const lngs = points.map((p) => p.lng)
  const latPad = padMeters / 111320
  const midLat = (Math.min(...lats) + Math.max(...lats)) / 2
  const lngPad = padMeters / (111320 * Math.cos((midLat * Math.PI) / 180))

  return {
    south: Math.min(...lats) - latPad,
    north: Math.max(...lats) + latPad,
    west: Math.min(...lngs) - lngPad,
    east: Math.max(...lngs) + lngPad,
  }
}

/** Énumère les tuiles couvrant les bornes, du zoom le plus large au plus fin. */
export function tilesForBounds(bounds, zMin = 14, zMax = 17, limit = TILE_BUDGET) {
  if (!bounds) return []
  const out = []
  for (let z = zMin; z <= zMax; z++) {
    const nw = lngLatToTile(bounds.west, bounds.north, z)
    const se = lngLatToTile(bounds.east, bounds.south, z)
    for (let x = nw.x; x <= se.x; x++) {
      for (let y = nw.y; y <= se.y; y++) {
        out.push({ z, x, y })
        if (out.length >= limit) return out
      }
    }
  }
  return out
}

export function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} o`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} Ko`
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`
}

export async function cacheStats() {
  if (!('caches' in window)) return { supported: false, tiles: 0, bytes: null }
  const cache = await caches.open(TILE_CACHE)
  const keys = await cache.keys()
  let bytes = 0
  if ('estimate' in navigator.storage) {
    try { bytes = (await navigator.storage.estimate()).usage ?? 0 } catch { /* ignore */ }
  }
  return { supported: true, tiles: keys.length, bytes }
}

/**
 * Télécharge les tuiles dans le même cache que celui servi par le service
 * worker. Les tuiles déjà présentes sont sautées : relancer ne re-télécharge
 * rien.
 */
export async function prefetchTiles(tiles, { onProgress, concurrency = 5, signal } = {}) {
  if (!('caches' in window)) throw new Error('Cache Storage indisponible')

  const cache = await caches.open(TILE_CACHE)
  const queue = [...tiles]
  const total = queue.length
  const acc = { done: 0, downloaded: 0, skipped: 0, failed: 0, bytes: 0 }

  async function worker() {
    for (;;) {
      if (signal?.aborted) return
      const t = queue.shift()
      if (!t) return
      const url = TILE_URL(t.z, t.x, t.y)
      try {
        if (await cache.match(url)) {
          acc.skipped++
        } else {
          const res = await fetch(url, { mode: 'cors', credentials: 'omit' })
          if (res.ok) {
            const blob = await res.clone().blob()
            acc.bytes += blob.size
            await cache.put(url, res)
            acc.downloaded++
          } else {
            acc.failed++
          }
        }
      } catch {
        acc.failed++
      }
      acc.done++
      onProgress?.({ ...acc, total })
    }
  }

  await Promise.all(Array.from({ length: Math.max(1, concurrency) }, worker))
  return { ...acc, total }
}
