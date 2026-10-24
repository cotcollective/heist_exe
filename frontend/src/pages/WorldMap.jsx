import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, Circle, Marker, useMap } from 'react-leaflet'
import L from 'leaflet'
import GlitchText from '../components/GlitchText'
import QRScanner from '../components/QRScanner'
import { worldApi } from '../api/client'
import { useMissionStore } from '../store/missionStore'

// Le monde = les caches orphelines, publiques. Le commun.
// Même règle que sur la chasse : on rend la ZONE, jamais le point.

const playerIcon = L.divIcon({
  className: '',
  html: `<div style="width:14px;height:14px;background:#a78bfa;border:2px solid #0a0a0a;border-radius:50%"></div>`,
  iconSize: [14, 14], iconAnchor: [7, 7],
})

function FitBounds({ caches }) {
  const map = useMap()
  useEffect(() => {
    if (!caches.length) return
    if (caches.length === 1) {
      map.setView([caches[0].lat, caches[0].lng], 15)
      return
    }
    const b = L.latLngBounds(caches.map((c) => [c.lat, c.lng]))
    map.fitBounds(b, { padding: [40, 40] })
  }, [caches, map])
  return null
}

export default function WorldMap() {
  const navigate = useNavigate()
  const playerName = useMissionStore((s) => s.playerName)

  const [caches, setCaches] = useState([])
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState('')
  const [selected, setSelected] = useState(null)

  // réclamation
  const [name, setName] = useState(playerName || '')
  const [scanning, setScanning] = useState(false)
  const [proof, setProof] = useState(null)
  const [claiming, setClaiming] = useState(false)
  const [result, setResult] = useState(null)

  const [me, setMe] = useState(null)

  useEffect(() => {
    worldApi.listCaches()
      .then((d) => setCaches(d))
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!navigator.geolocation) return
    navigator.geolocation.getCurrentPosition(
      (p) => setMe([p.coords.latitude, p.coords.longitude]),
      () => {},
      { enableHighAccuracy: true, maximumAge: 10000 }
    )
  }, [])

  const center = useMemo(() => {
    if (caches.length) return [caches[0].lat, caches[0].lng]
    return [45.568, -73.55]
  }, [caches])

  function openCache(c) {
    setSelected(c)
    setResult(null)
    setProof(null)
    setScanning(false)
  }

  async function doClaim(withProof) {
    if (!selected) return
    if (!name.trim()) { setResult({ kind: 'err', msg: "Donne-toi un nom d'agent." }); return }
    setClaiming(true)
    try {
      const r = await worldApi.claim(selected.id, name.trim(), withProof)
      setResult({ kind: r.claimed ? 'ok' : 'dup', data: r })
      if (r.claimed) {
        setCaches((cs) => cs.map((c) =>
          c.id === selected.id ? { ...c, claim_count: r.claim_count } : c
        ))
        setSelected((s) => (s ? { ...s, claim_count: r.claim_count } : s))
      }
    } catch (e) {
      setResult({ kind: 'err', msg: e.message })
    } finally {
      setClaiming(false)
    }
  }

  if (scanning) {
    return (
      <div className="hx-screen flex flex-col p-4">
        <div className="text-hx-sub text-xs tracking-widest mb-3">// SCAN DE LA PREUVE</div>
        <QRScanner
          onResult={(txt) => { setProof(txt); setScanning(false); doClaim(txt) }}
          onClose={() => setScanning(false)}
          label="Scanne le QR caché sur place"
        />
      </div>
    )
  }

  return (
    <div className="hx-screen flex flex-col">
      <div className="px-4 pt-safe pb-3 border-b border-hx-border flex items-center justify-between">
        <div>
          <div className="text-hx-sub text-xs tracking-widest">// LE MONDE</div>
          <GlitchText text="CACHES PUBLIQUES" autoPlay className="text-sm font-bold text-hx-text" />
        </div>
        <button onClick={() => navigate('/')} className="text-hx-dim text-xs font-mono">
          ← SORTIE
        </button>
      </div>

      <div className="px-4 py-2 border-b border-hx-border text-hx-dim text-xs font-mono">
        {loading ? 'CHARGEMENT…' : `${caches.length} cache${caches.length === 1 ? '' : 's'} dans le monde`}
        {err && <span className="text-hx-amber"> — {err}</span>}
      </div>

      <div className="flex-1 relative">
        <MapContainer
          center={center}
          zoom={14}
          className="w-full h-full"
          zoomControl={false}
          attributionControl={false}
        >
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <FitBounds caches={caches} />

          {caches.map((c) => (
            <Circle
              key={c.id}
              center={[c.lat, c.lng]}
              radius={c.radius_meters}
              eventHandlers={{ click: () => openCache(c) }}
              pathOptions={{
                color: selected?.id === c.id ? '#f59e0b' : '#00d4aa',
                fillColor: selected?.id === c.id ? '#f59e0b' : '#00d4aa',
                fillOpacity: 0.08,
                weight: 2,
                dashArray: '8 8',
              }}
            />
          ))}

          {me && <Marker position={me} icon={playerIcon} />}
        </MapContainer>

        {!loading && caches.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="text-center px-8">
              <div className="text-hx-dim text-xs font-mono">
                // aucune cache plantée pour l'instant
              </div>
              <div className="text-hx-dim text-xs font-mono mt-2 opacity-60">
                les missions qui finissent en laissent derrière elles
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bandeau : accès tactile et accessible, en plus des cercles sur la carte */}
      {caches.length > 0 && (
        <div className="border-t border-hx-border px-3 py-2 flex gap-2 overflow-x-auto">
          {caches.map((c) => (
            <button
              key={c.id}
              onClick={() => openCache(c)}
              className={`shrink-0 px-3 py-1.5 rounded border text-xs font-mono transition-colors ${
                selected?.id === c.id
                  ? 'border-hx-teal text-hx-teal'
                  : 'border-hx-border text-hx-dim'
              }`}
            >
              {c.title}
              <span className="opacity-60"> · {c.claim_count}</span>
            </button>
          ))}
        </div>
      )}

      {/* Détail */}
      {selected && (
        <div className="border-t border-hx-border bg-hx-bg px-4 py-3">
          <div className="flex items-start justify-between mb-2">
            <div className="text-hx-text text-sm font-bold font-mono">{selected.title}</div>
            <button onClick={() => setSelected(null)} className="text-hx-dim text-xs">✕</button>
          </div>

          {selected.hint && (
            <div className="text-hx-sub text-xs font-mono border-l-2 border-hx-border pl-3 mb-2">
              {selected.hint}
            </div>
          )}

          <div className="text-hx-dim text-xs font-mono mb-3">
            zone ~{selected.radius_meters}m
            {' · '}trouvée {selected.claim_count}×
            {selected.owner_label && <> {' · '}plantée par {selected.owner_label}</>}
            {selected.requires_proof && <span className="text-hx-amber"> · preuve QR requise</span>}
          </div>

          {result?.kind === 'ok' && (
            <div className="text-hx-green text-xs font-mono mb-2">
              TROUVÉE ✓ — {result.data.claim_count} réclamation
              {result.data.claim_count > 1 ? 's' : ''}
              {result.data.proven ? ' · preuve validée' : ' · non prouvée'}
            </div>
          )}
          {result?.kind === 'dup' && (
            <div className="text-hx-amber text-xs font-mono mb-2">
              Tu l'as déjà réclamée. Elle reste ouverte aux autres.
            </div>
          )}
          {result?.kind === 'err' && (
            <div className="text-hx-amber text-xs font-mono mb-2">// {result.msg}</div>
          )}

          <div className="flex gap-2">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="ton nom d'agent"
              className="flex-1 bg-hx-panel border border-hx-border rounded px-3 py-2 text-xs font-mono text-hx-text"
            />
            <button
              disabled={claiming}
              onClick={() => selected.requires_proof ? setScanning(true) : doClaim(null)}
              className="px-4 py-2 bg-hx-teal text-hx-bg font-mono text-xs font-bold rounded disabled:opacity-50"
            >
              {claiming ? '…' : selected.requires_proof ? 'SCANNER ▶' : 'RÉCLAMER ▶'}
            </button>
          </div>

          {proof && <div className="text-hx-dim text-xs font-mono mt-2">preuve: {proof}</div>}
        </div>
      )}
    </div>
  )
}
