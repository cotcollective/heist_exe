import { useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, Circle, Popup } from 'react-leaflet'
import L from 'leaflet'
import { useEffect, useRef } from 'react'
import { useMap } from 'react-leaflet'
import { useMissionStore } from '../store/missionStore'
import Countdown from '../components/Countdown'
import GlitchText from '../components/GlitchText'
import NavArrow from '../components/NavArrow'
import { useGeoPosition } from '../hooks/useGeoPosition'

// Import statique conditionné à la compile-time : zéro overhead en prod
import DevGpsPanel from '../components/DevGpsPanel'
const DEV_GPS = import.meta.env.VITE_DEV_GPS === 'true'

// ── Icônes Leaflet ────────────────────────────────────────────────────────────
// Pas d'icône pour la cible : le centre du waypoint n'est JAMAIS rendu.
const playerIcon = L.divIcon({
  className: '',
  html: `<div style="width:14px;height:14px;background:#a78bfa;border:2px solid #0a0a0a;border-radius:50%"></div>`,
  iconSize: [14, 14], iconAnchor: [7, 7],
})

function FlyTo({ position }) {
  const map = useMap()
  useEffect(() => { if (position) map.flyTo(position, 17, { duration: 1.5 }) }, [position]) // eslint-disable-line
  return null
}

// ── Composant principal ───────────────────────────────────────────────────────
export default function WaypointHunt() {
  const navigate = useNavigate()
  const mission = useMissionStore((s) => s.mission)
  const currentWaypoint = useMissionStore((s) => s.currentWaypoint)

  const wp = currentWaypoint

  const { playerPos, edgeDistance, bearing, inRange, geoError, inject } = useGeoPosition(wp)

  // Affichage COARSE, et uniquement la distance au BORD de la zone.
  // Un compteur précis au mètre transforme le téléphone en détecteur de métaux :
  // tu marches et tu regardes le chiffre descendre. On le tue.
  const coarse = edgeDistance === null ? null : Math.round(edgeDistance / 10) * 10

  if (!mission || !wp) { navigate('/'); return null }

  const mapCenter = [wp.lat, wp.lng]
  const totalWps = mission.waypoints?.length ?? 0

  return (
    <div className="hx-screen flex flex-col">

      {/* ── Header ── */}
      <div className="px-4 pt-safe pb-3 border-b border-hx-border">
        <div className="flex items-center justify-between mb-2">
          <div>
            <div className="text-hx-sub text-xs tracking-widest">
              WAYPOINT {wp.order + 1}/{totalWps}
            </div>
            <GlitchText
              text={wp.title.toUpperCase()}
              autoPlay
              className="text-sm font-bold text-hx-text"
            />
          </div>
          <div className="text-right">
            <div className={`text-2xl font-mono font-bold tabular-nums ${inRange
                ? 'text-hx-green'
                : coarse !== null && coarse < 100
                  ? 'text-hx-amber'
                  : 'text-hx-teal'
              }`}>
              {inRange ? 'ZONE' : coarse !== null ? `~${coarse}m` : '---'}
            </div>
            <div className={`text-xs tracking-widest ${inRange
                ? 'text-hx-green animate-blink'
                : 'text-hx-dim'
              }`}>
              {inRange ? 'CHERCHE' : coarse !== null ? 'APPROCHE' : 'GPS…'}
            </div>
          </div>
        </div>
        <Countdown onTimeout={() => navigate('/reward')} />
      </div>

      {/* ── Map + NavArrow overlay ── */}
      <div className="flex-1 relative">
        <MapContainer
          center={mapCenter}
          zoom={17}
          className="w-full h-full"
          zoomControl={false}
          attributionControl={false}
        >
          <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {/* ZONE DE RECHERCHE — pas une cible.
              Aucun marqueur au centre : on donne l'aire, jamais le point.
              Le joueur doit combler l'écart avec ses yeux et ses pieds. */}
          <Circle
            center={[wp.lat, wp.lng]}
            radius={wp.radius_meters}
            pathOptions={{
              color: '#00d4aa',
              fillColor: '#00d4aa',
              fillOpacity: 0.06,
              weight: 2,
              dashArray: '8 8',
            }}
          >
            <Popup>Zone de recherche — la cache est quelque part ici.</Popup>
          </Circle>
          {playerPos && <Marker position={playerPos} icon={playerIcon} />}
          <FlyTo position={playerPos ?? mapCenter} />
        </MapContainer>

        {/* Grosse flèche Crazy Taxi — overlay positionné absolut sur la carte */}
        <NavArrow bearing={bearing} inRange={inRange} />
      </div>

      {/* ── Footer ── */}
      <div className="px-4 py-4 border-t border-hx-border bg-hx-bg">
        {geoError && (
          <div className="text-hx-amber text-xs font-mono mb-3">// {geoError}</div>
        )}
        {wp.hint && (
          <div className="text-hx-sub text-xs font-mono mb-3 border-l-2 border-hx-border pl-3">
            {wp.hint}
          </div>
        )}
        <button
          disabled={!inRange}
          data-testid="enter-enigma"
          onClick={() => navigate(`/enigma/${wp.id}`)}
          className={`w-full py-3 font-mono text-sm font-bold rounded transition-all ${inRange
              ? 'bg-hx-teal text-hx-bg hover:bg-hx-teal-d animate-pulse-teal'
              : 'bg-hx-muted text-hx-dim cursor-not-allowed'
            }`}
        >
          {inRange ? 'CHERCHER ▶' : coarse !== null ? `APPROCHE-TOI (~${coarse}m)` : 'GPS…'}
        </button>
      </div>

      {/* ── Dev GPS Panel — UNIQUEMENT en mode dev, tree-shaken en prod ── */}
      {DEV_GPS && (
        <DevGpsPanel
          waypoints={mission.waypoints}
          currentWpId={wp.id}
          onInject={inject}
        />
      )}
    </div>
  )
}
