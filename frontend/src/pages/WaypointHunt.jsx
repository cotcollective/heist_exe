import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, Circle, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import { useMissionStore } from '../store/missionStore'
import Countdown from '../components/Countdown'
import GlitchText from '../components/GlitchText'

// Icône custom teal pour le waypoint cible
const targetIcon = L.divIcon({
  className: '',
  html: `<div style="width:20px;height:20px;background:#00d4aa;border:2px solid #0a0a0a;border-radius:50%;box-shadow:0 0 0 3px rgba(0,212,170,0.3)"></div>`,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
})

const playerIcon = L.divIcon({
  className: '',
  html: `<div style="width:14px;height:14px;background:#a78bfa;border:2px solid #0a0a0a;border-radius:50%"></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7],
})

function FlyTo({ position }) {
  const map = useMap()
  useEffect(() => { if (position) map.flyTo(position, 17, { duration: 1.5 }) }, [position]) // eslint-disable-line
  return null
}

function distanceMeters(lat1, lng1, lat2, lng2) {
  const R = 6371000
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLng = ((lng2 - lng1) * Math.PI) / 180
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLng/2)**2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
}

export default function WaypointHunt() {
  const navigate          = useNavigate()
  const mission           = useMissionStore((s) => s.mission)
  const currentWaypoint   = useMissionStore((s) => s.currentWaypoint)
  const completedWaypoints= useMissionStore((s) => s.completedWaypoints)

  const [playerPos, setPlayerPos]   = useState(null)
  const [distance, setDistance]     = useState(null)
  const [inRange, setInRange]       = useState(false)
  const [geoError, setGeoError]     = useState('')

  const wp = currentWaypoint

  useEffect(() => {
    if (!navigator.geolocation) { setGeoError('GPS non disponible'); return }
    const watchId = navigator.geolocation.watchPosition(
      (pos) => {
        const { latitude: lat, longitude: lng } = pos.coords
        setPlayerPos([lat, lng])
        if (wp) {
          const d = distanceMeters(lat, lng, wp.lat, wp.lng)
          setDistance(Math.round(d))
          setInRange(d <= wp.radius_meters)
        }
      },
      () => setGeoError('Autorise le GPS pour la mission'),
      { enableHighAccuracy: true, maximumAge: 5000 }
    )
    return () => navigator.geolocation.clearWatch(watchId)
  }, [wp])

  if (!mission || !wp) { navigate('/'); return null }

  const mapCenter = [wp.lat, wp.lng]
  const totalWps  = mission.waypoints?.length ?? 0
  const doneCount = completedWaypoints.length

  return (
    <div className="hx-screen flex flex-col">
      {/* Header compact */}
      <div className="px-4 pt-safe pb-3 border-b border-hx-border">
        <div className="flex items-center justify-between mb-2">
          <div>
            <div className="text-hx-sub text-xs tracking-widest">WAYPOINT {wp.order + 1}/{totalWps}</div>
            <GlitchText text={wp.title.toUpperCase()} autoPlay className="text-sm font-bold text-hx-text" />
          </div>
          <div className="text-right">
            <div className={`text-2xl font-mono font-bold tabular-nums ${
              inRange ? 'text-hx-green' : distance !== null && distance < 100 ? 'text-hx-amber' : 'text-hx-teal'
            }`}>
              {distance !== null ? `${distance}m` : '---'}
            </div>
            {inRange && <div className="text-hx-green text-xs animate-blink">EN PORTÉE</div>}
          </div>
        </div>
        <Countdown onTimeout={() => navigate('/reward')} />
      </div>

      {/* Map OSM */}
      <div className="flex-1 relative">
        <MapContainer
          center={mapCenter}
          zoom={17}
          className="w-full h-full"
          zoomControl={false}
          attributionControl={false}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; OpenStreetMap contributors'
          />
          {/* Zone de détection */}
          <Circle
            center={[wp.lat, wp.lng]}
            radius={wp.radius_meters}
            pathOptions={{ color: '#00d4aa', fillColor: '#00d4aa', fillOpacity: 0.1, weight: 1.5 }}
          />
          {/* Marker waypoint cible */}
          <Marker position={[wp.lat, wp.lng]} icon={targetIcon}>
            <Popup>{wp.title}</Popup>
          </Marker>
          {/* Position joueur */}
          {playerPos && (
            <Marker position={playerPos} icon={playerIcon} />
          )}
          <FlyTo position={playerPos ?? mapCenter} />
        </MapContainer>
      </div>

      {/* Bas de page */}
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
          data-testid="enter-enigma" onClick={() => navigate(`/enigma/${wp.id}`)}
          className={`w-full py-3 font-mono text-sm font-bold rounded transition-all ${
            inRange
              ? 'bg-hx-teal text-hx-bg hover:bg-hx-teal-d animate-pulse-teal'
              : 'bg-hx-muted text-hx-dim cursor-not-allowed'
          }`}
        >
          {inRange ? 'ACCÉDER À L\'ÉNIGME ▶' : `APPROCHE-TOI (${distance ?? '?'}m restants)`}
        </button>
      </div>
    </div>
  )
}
