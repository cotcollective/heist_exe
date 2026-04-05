/**
 * DevGpsPanel — Panneau de simulation GPS (DEV ONLY).
 * Visible uniquement quand VITE_DEV_GPS=true.
 * Permet de teleporter la position fictive du joueur sur n'importe quel waypoint.
 */
import { useState } from 'react'

export default function DevGpsPanel({ waypoints, currentWpId, onInject }) {
    const [customLat, setCustomLat] = useState('')
    const [customLng, setCustomLng] = useState('')
    const [open, setOpen] = useState(true)

    return (
        <div className="dev-gps-panel">
            {/* Toggle */}
            <button
                className="dev-gps-toggle"
                onClick={() => setOpen((o) => !o)}
                aria-label="Toggle dev GPS panel"
            >
                🛰 DEV GPS {open ? '▼' : '▲'}
            </button>

            {open && (
                <div className="dev-gps-body">
                    {/* Waypoints rapides */}
                    <div className="dev-gps-section-label">// TÉLÉPORTER SUR WAYPOINT</div>
                    <div className="dev-gps-wp-list">
                        {waypoints?.map((wp) => (
                            <button
                                key={wp.id}
                                className={`dev-gps-wp-btn ${wp.id === currentWpId ? 'active' : ''}`}
                                onClick={() => onInject(wp.lat, wp.lng)}
                            >
                                📍 WP{wp.order} — {wp.title}
                            </button>
                        ))}
                        {/* Bouton pour se téléporter exactement DANS la zone (radius -1m) */}
                        {waypoints?.map((wp) => (
                            <button
                                key={`in-${wp.id}`}
                                className="dev-gps-wp-btn range"
                                onClick={() => {
                                    // Offset de 0.5m vers le nord pour être dans la zone
                                    const offsetLat = wp.lat + 0.000004
                                    onInject(offsetLat, wp.lng)
                                }}
                            >
                                ✅ WP{wp.order} — EN PORTÉE
                            </button>
                        ))}
                    </div>

                    {/* Coordonnées custom */}
                    <div className="dev-gps-section-label">// COORDONNÉES MANUELLES</div>
                    <div className="dev-gps-custom">
                        <input
                            className="dev-gps-input"
                            placeholder="lat (ex: 45.5679)"
                            value={customLat}
                            onChange={(e) => setCustomLat(e.target.value)}
                        />
                        <input
                            className="dev-gps-input"
                            placeholder="lng (ex: -73.5491)"
                            value={customLng}
                            onChange={(e) => setCustomLng(e.target.value)}
                        />
                        <button
                            className="dev-gps-inject-btn"
                            disabled={!customLat || !customLng}
                            onClick={() => onInject(parseFloat(customLat), parseFloat(customLng))}
                        >
                            INJECTER 🎯
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}
