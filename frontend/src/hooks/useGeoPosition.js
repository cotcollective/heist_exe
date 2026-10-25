/**
 * useGeoPosition — Hook GPS unifié avec support Dev Mode.
 *
 * L'ACCURACY fait partie du résultat, et ce n'est pas un détail.
 *
 * Le navigateur peut rendre une position obtenue par WiFi ou par IP, avec
 * une incertitude de plusieurs centaines de mètres — surtout sur un
 * ordinateur de bureau, ou à l'intérieur. L'ancienne version l'ignorait :
 * elle dessinait un point net, et le joueur lisait « l'app me place au
 * mauvais endroit ». Ce n'était pas la carte qui mentait, c'était nous qui
 * affirmions une précision que la mesure n'avait pas.
 *
 * En production  : wraps navigator.geolocation.watchPosition
 * En dev (VITE_DEV_GPS=true) : prioritise la position simulée injectée via inject()
 */
import { useState, useEffect, useCallback } from 'react'

const DEV_GPS = import.meta.env.VITE_DEV_GPS === 'true'

function distanceMeters(lat1, lng1, lat2, lng2) {
    const R = 6371000
    const dLat = ((lat2 - lat1) * Math.PI) / 180
    const dLng = ((lng2 - lng1) * Math.PI) / 180
    const a =
        Math.sin(dLat / 2) ** 2 +
        Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLng / 2) ** 2
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

export function calcBearing(lat1, lng1, lat2, lng2) {
    const dLng = ((lng2 - lng1) * Math.PI) / 180
    const y = Math.sin(dLng) * Math.cos((lat2 * Math.PI) / 180)
    const x =
        Math.cos((lat1 * Math.PI) / 180) * Math.sin((lat2 * Math.PI) / 180) -
        Math.sin((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.cos(dLng)
    return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360
}

/**
 * Traduit une erreur GPS en une phrase qui dit quoi faire.
 *
 * Le code 1 (PERMISSION_DENIED) est le seul que l'utilisateur peut corriger
 * lui-même, et c'est le seul qu'on ne voyait pas : toutes les erreurs
 * tombaient dans le même message, sans issue. Sur un téléphone, un refus
 * accidentel de la bulle de permission laissait l'écran mort.
 */
function humanGeoError(err) {
    if (!err) return 'GPS indisponible'
    switch (err.code) {
        case 1: return 'GPS bloqué — autorise la position dans les réglages du navigateur, puis réessaie'
        case 2: return 'Position introuvable — sors à découvert et réessaie'
        case 3: return 'Le GPS met trop de temps — réessaie'
        default: return 'GPS indisponible'
    }
}

export function useGeoPosition(wp) {
    const [playerPos, setPlayerPos] = useState(null)
    const [distance, setDistance] = useState(null)      // brut, centre du waypoint
    const [edgeDistance, setEdgeDistance] = useState(null) // distance au BORD de la zone
    const [bearing, setBearing] = useState(null)
    const [inRange, setInRange] = useState(false)       // = DANS la zone de recherche
    const [geoError, setGeoError] = useState('')
    const [accuracy, setAccuracy] = useState(null)   // rayon d'incertitude, en mètres
    const [simPos, setSimPos] = useState(null) // [lat, lng] simulées
    const [simAccuracy, setSimAccuracy] = useState(null) // précision simulée, mètres
    const [retryTick, setRetryTick] = useState(0)  // relance le watch

    // Injection externe (DevGpsPanel)
    const inject = useCallback((lat, lng, acc = null) => {
        setSimPos([lat, lng])
        setSimAccuracy(acc)
    }, [])

    useEffect(() => {
        function update(lat, lng) {
            setPlayerPos([lat, lng])
            if (wp) {
                const d = distanceMeters(lat, lng, wp.lat, wp.lng)
                const b = calcBearing(lat, lng, wp.lat, wp.lng)
                setDistance(Math.round(d))
                // Le joueur navigue vers la ZONE, pas vers le point.
                setEdgeDistance(Math.max(0, Math.round(d - wp.radius_meters)))
                setBearing(Math.round(b))
                setInRange(d <= wp.radius_meters)
            }
        }

        // Dev mode : position simulée en priorité
        if (DEV_GPS && simPos) {
            // L'accuracy simulée passe par le même champ que la vraie : on
            // teste le rendu, pas un chemin parallèle qui divergerait.
            setAccuracy(simAccuracy)
            update(simPos[0], simPos[1])
            return
        }

        if (!navigator.geolocation) {
            setGeoError('GPS non disponible')
            return
        }

        const watchId = navigator.geolocation.watchPosition(
            (pos) => {
                const { latitude: lat, longitude: lng, accuracy: acc } = pos.coords
                setGeoError('')
                setAccuracy(acc ?? null)
                update(lat, lng)
            },
            (err) => setGeoError(humanGeoError(err)),
            { enableHighAccuracy: true, maximumAge: 5000, timeout: 15000 }
        )
        return () => navigator.geolocation.clearWatch(watchId)
    }, [wp, simPos, simAccuracy, retryTick])

    const retry = useCallback(() => {
        setGeoError('')
        setAccuracy(null)
        setRetryTick((t) => t + 1)
    }, [])

    return { playerPos, accuracy, distance, edgeDistance, bearing, inRange, geoError, inject, retry, DEV_GPS }
}
