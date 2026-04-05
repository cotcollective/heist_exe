import { useState, useCallback } from 'react'
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import { HxInput, HxButton, HxDivider, HxBadge } from './HxAtoms'

const pinIcon = (color = '#00d4aa') => L.divIcon({
  className: '',
  html: `<div style="width:16px;height:16px;background:${color};border:2px solid #0a0a0a;border-radius:50%;box-shadow:0 0 0 3px ${color}33"></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
})

function MapPicker({ lat, lng, onChange }) {
  useMapEvents({
    click(e) { onChange(e.latlng.lat, e.latlng.lng) },
  })
  return lat && lng
    ? <Marker position={[lat, lng]} icon={pinIcon()} />
    : null
}

const EMPTY_ENIGMA = { question: '', answer: '', hint: '' }
const DEFAULT_CENTER = [45.5680, -73.5490] // Tétreaultville

export default function WaypointEditor({ waypoint, index, onUpdate, onRemove, onMoveUp, onMoveDown, isFirst, isLast }) {
  const [expanded, setExpanded] = useState(index === 0)

  const upd = useCallback((field, value) => {
    onUpdate({ ...waypoint, [field]: value })
  }, [waypoint, onUpdate])

  const updEnigma = useCallback((field, value) => {
    const enigma = waypoint.enigma ? { ...waypoint.enigma, [field]: value } : { ...EMPTY_ENIGMA, [field]: value }
    onUpdate({ ...waypoint, enigma })
  }, [waypoint, onUpdate])

  const toggleEnigma = () => {
    onUpdate({ ...waypoint, enigma: waypoint.enigma ? null : { ...EMPTY_ENIGMA } })
  }

  const mapCenter = (waypoint.lat && waypoint.lng)
    ? [waypoint.lat, waypoint.lng]
    : DEFAULT_CENTER

  return (
    <div className="border border-hx-border rounded overflow-hidden">
      {/* Waypoint header */}
      <div
        className="flex items-center gap-3 px-3 py-2.5 bg-hx-surface cursor-pointer select-none"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-hx-amber text-[10px] font-mono tracking-widest">
              WP{index}
            </span>
            {waypoint.enigma && <HxBadge variant="teal">ÉNIGME</HxBadge>}
            {!waypoint.enigma && <HxBadge variant="default">FINAL</HxBadge>}
          </div>
          <div className="text-hx-text text-sm font-mono truncate mt-0.5">
            {waypoint.title || <span className="text-hx-dim italic">Sans titre</span>}
          </div>
        </div>

        {/* Réordonner */}
        <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
          <button disabled={isFirst} onClick={onMoveUp}
            className="text-hx-dim hover:text-hx-text disabled:opacity-20 font-mono text-sm px-1">↑</button>
          <button disabled={isLast} onClick={onMoveDown}
            className="text-hx-dim hover:text-hx-text disabled:opacity-20 font-mono text-sm px-1">↓</button>
          <button onClick={onRemove}
            className="text-hx-dim hover:text-hx-red font-mono text-sm px-1 ml-1">✕</button>
        </div>

        <span className="text-hx-dim font-mono text-sm">{expanded ? '▲' : '▼'}</span>
      </div>

      {/* Corps expandable */}
      {expanded && (
        <div className="px-3 pb-4 pt-3 border-t border-hx-border space-y-4">

          <HxInput
            label="TITRE DU WAYPOINT"
            value={waypoint.title}
            onChange={(e) => upd('title', e.target.value)}
            placeholder="ex: Parc L.-O.-Taillon"
            required
          />

          <HxInput
            label="INDICE / HINT"
            value={waypoint.hint ?? ''}
            onChange={(e) => upd('hint', e.target.value)}
            placeholder="Ce que voit l'agent en arrivant…"
            rows={2}
            hint="Affiché sous la map pour guider l'agent vers l'emplacement exact."
          />

          {/* Map de placement GPS */}
          <div>
            <div className="text-[10px] tracking-widest text-hx-sub font-mono mb-2">
              POSITION GPS — clique sur la map pour placer
            </div>
            <div className="rounded overflow-hidden border border-hx-border" style={{ height: 200 }}>
              <MapContainer
                center={mapCenter}
                zoom={17}
                className="w-full h-full"
                zoomControl={false}
                attributionControl={false}
              >
                <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                <MapPicker
                  lat={waypoint.lat}
                  lng={waypoint.lng}
                  onChange={(lat, lng) => onUpdate({ ...waypoint, lat, lng })}
                />
              </MapContainer>
            </div>
            <div className="flex gap-3 mt-2">
              <HxInput
                label="LAT"
                value={waypoint.lat ?? ''}
                onChange={(e) => upd('lat', parseFloat(e.target.value) || '')}
                placeholder="45.5680"
                type="number"
                className="flex-1"
              />
              <HxInput
                label="LNG"
                value={waypoint.lng ?? ''}
                onChange={(e) => upd('lng', parseFloat(e.target.value) || '')}
                placeholder="-73.5490"
                type="number"
                className="flex-1"
              />
              <HxInput
                label="RAYON (m)"
                value={waypoint.radius_meters ?? 30}
                onChange={(e) => upd('radius_meters', parseInt(e.target.value) || 30)}
                placeholder="30"
                type="number"
                className="w-24"
              />
            </div>
          </div>

          <HxDivider label="ÉNIGME" />

          {/* Toggle énigme */}
          <div className="flex items-center justify-between">
            <span className="text-hx-sub text-xs font-mono">
              {waypoint.enigma ? 'Énigme active' : 'Pas d\'énigme (waypoint final)'}
            </span>
            <button
              onClick={toggleEnigma}
              className={`font-mono text-xs px-3 py-1 rounded border transition-colors ${
                waypoint.enigma
                  ? 'border-hx-teal text-hx-teal hover:bg-hx-teal/10'
                  : 'border-hx-border text-hx-dim hover:border-hx-dim'
              }`}
            >
              {waypoint.enigma ? 'RETIRER' : '+ AJOUTER'}
            </button>
          </div>

          {waypoint.enigma && (
            <div className="space-y-3 border-l-2 border-hx-teal/40 pl-3">
              <HxInput
                label="QUESTION / ÉNIGME"
                value={waypoint.enigma.question}
                onChange={(e) => updEnigma('question', e.target.value)}
                placeholder="Compte les lattes de bois × numéro civique…"
                rows={3}
                required
              />
              <HxInput
                label="RÉPONSE (en clair — sera hashée)"
                value={waypoint.enigma.answer}
                onChange={(e) => updEnigma('answer', e.target.value)}
                placeholder="ex: 84"
                hint="Insensible à la casse et aux espaces."
                required
              />
              <HxInput
                label="INDICE (optionnel)"
                value={waypoint.enigma.hint ?? ''}
                onChange={(e) => updEnigma('hint', e.target.value)}
                placeholder="ex: Le numéro est sur la façade principale."
              />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
