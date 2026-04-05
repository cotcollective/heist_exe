/**
 * useGeoPosition — Hook GPS unifié avec support Dev Mode.
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

export function useGeoPosition(wp) {
    const [playerPos, setPlayerPos] = useState(null)
    const [distance, setDistance] = useState(null)
    const [bearing, setBearing] = useState(null)
    const [inRange, setInRange] = useState(false)
    const [geoError, setGeoError] = useState('')
    const [simPos, setSimPos] = useState(null) // [lat, lng] simulées

    // Injection externe (DevGpsPanel)
    const inject = useCallback((lat, lng) => {
        setSimPos([lat, lng])
    }, [])

    useEffect(() => {
        function update(lat, lng) {
            setPlayerPos([lat, lng])
            if (wp) {
                const d = distanceMeters(lat, lng, wp.lat, wp.lng)
                const b = calcBearing(lat, lng, wp.lat, wp.lng)
                setDistance(Math.round(d))
                setBearing(Math.round(b))
                setInRange(d <= wp.radius_meters)
            }
        }

        // Dev mode : position simulée en priorité
        if (DEV_GPS && simPos) {
            update(simPos[0], simPos[1])
            return
        }

        if (!navigator.geolocation) {
            setGeoError('GPS non disponible')
            return
        }

        const watchId = navigator.geolocation.watchPosition(
            (pos) => {
                const { latitude: lat, longitude: lng } = pos.coords
                update(lat, lng)
            },
            () => setGeoError('Autorise le GPS pour la mission'),
            { enableHighAccuracy: true, maximumAge: 5000 }
        )
        return () => navigator.geolocation.clearWatch(watchId)
    }, [wp, simPos])

    return { playerPos, distance, bearing, inRange, geoError, inject, DEV_GPS }
}
