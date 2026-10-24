import { useEffect, useMemo, useRef, useState } from 'react'
import {
  boundsFromPoints, tilesForBounds, prefetchTiles, cacheStats,
  formatBytes, BYTES_PER_TILE, TILE_BUDGET,
} from '../lib/tiles'

/**
 * OfflineZone — télécharge les tuiles de la zone d'une mission avant de
 * partir. À faire à la maison, sur le wifi, pendant que le temps tourne
 * encore.
 */
export default function OfflineZone({ points }) {
  const [stats, setStats] = useState(null)
  const [progress, setProgress] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const abortRef = useRef(null)

  const bounds = useMemo(() => boundsFromPoints(points, 400), [points])
  const tiles = useMemo(() => tilesForBounds(bounds, 14, 17, TILE_BUDGET), [bounds])

  useEffect(() => {
    cacheStats().then(setStats).catch(() => setStats({ supported: false, tiles: 0 }))
  }, [])

  useEffect(() => () => abortRef.current?.abort(), [])

  async function download() {
    setError(''); setResult(null); setProgress({ done: 0, total: tiles.length })
    const controller = new AbortController()
    abortRef.current = controller
    try {
      const res = await prefetchTiles(tiles, {
        onProgress: setProgress,
        signal: controller.signal,
      })
      setResult(res)
      setStats(await cacheStats())
    } catch (e) {
      setError(e.message)
    } finally {
      setProgress(null)
    }
  }

  if (!bounds) return null

  const running = progress !== null
  const pct = running && progress.total ? Math.round((progress.done / progress.total) * 100) : 0

  return (
    <section className="border border-hx-border rounded p-4 mb-6">
      <div className="text-hx-sub text-xs tracking-widest mb-2">// HORS LIGNE</div>
      <p className="text-hx-dim text-xs font-sans leading-relaxed mb-3">
        Télécharge la carte de la zone avant de partir. Sans réseau, la carte
        reste utilisable et le GPS continue de fonctionner.
      </p>

      <div className="flex items-center justify-between text-xs font-mono text-hx-dim mb-3">
        <span>{tiles.length} tuiles · ~{formatBytes(tiles.length * BYTES_PER_TILE)}</span>
        {stats?.supported && <span>{stats.tiles} en cache</span>}
      </div>

      <p className="text-[11px] text-hx-sub leading-relaxed mb-3">
        Plafonné à {TILE_BUDGET} tuiles : la politique d'usage des tuiles OSM
        interdit les téléchargements massifs.
      </p>

      <button
        onClick={download}
        disabled={running || tiles.length === 0}
        className="w-full py-3 rounded font-mono text-xs font-bold bg-hx-teal text-hx-bg disabled:opacity-40"
      >
        {running ? `TÉLÉCHARGEMENT ${pct}%` : '⤓ TÉLÉCHARGER LA ZONE'}
      </button>

      {running && (
        <div className="mt-2 h-1 bg-hx-border rounded overflow-hidden">
          <div className="h-full bg-hx-teal transition-all" style={{ width: `${pct}%` }} />
        </div>
      )}

      {result && !running && (
        <div className="mt-3 text-xs font-mono text-hx-green">
          {result.downloaded} téléchargées · {result.skipped} déjà en cache
          {result.failed > 0 && <span className="text-hx-amber"> · {result.failed} échecs</span>}
        </div>
      )}

      {error && <div className="mt-2 text-xs font-mono text-hx-amber">// {error}</div>}
    </section>
  )
}
