const BASE = '/api'

async function request(method, path, body, token) {
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  let fetchBody
  if (body instanceof FormData) {
    fetchBody = body
  } else if (body) {
    headers['Content-Type'] = 'application/json'
    fetchBody = JSON.stringify(body)
  }

  const res = await fetch(`${BASE}${path}`, { method, headers, body: fetchBody })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? 'Erreur réseau')
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  auth:               (missionId, pin, playerName) =>
    request('POST', '/missions/auth', { mission_id: missionId, pin, player_name: playerName }),
  listActive:         () => request('GET', '/missions/active'),
  getCurrentWaypoint: (token) => request('GET', '/waypoints/current', null, token),
  submitAnswer:       (waypointId, answer, token) =>
    request('POST', '/waypoints/answer', { waypoint_id: waypointId, answer }, token),
}

export const adminApi = {
  listMissions:  (key) => request('GET', '/admin/missions', null, key),
  createMission: (key, payload) => request('POST', '/admin/missions', payload, key),
  deleteMission: (key, id) => request('DELETE', `/admin/missions/${id}`, null, key),
  uploadAudio:   (key, missionId, file) => {
    const fd = new FormData()
    fd.append('file', file)
    return request('POST', `/upload/audio/${missionId}`, fd, key)
  },
}

export function createCountdownSocket(missionId, sessionId, durationSeconds, callbacks) {
  const proto  = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const host   = import.meta.env.DEV ? 'localhost:8000' : window.location.host
  const prefix = import.meta.env.DEV ? '' : '/api'
  const ws     = new WebSocket(`${proto}://${host}${prefix}/ws/countdown/${missionId}/${sessionId}`)

  ws.onopen    = () => ws.send(JSON.stringify({ action: 'start', duration_seconds: durationSeconds }))
  ws.onmessage = (e) => {
    const data = JSON.parse(e.data)
    if (data.type === 'tick')    callbacks.onTick?.(data.remaining_seconds, data.percent)
    if (data.type === 'timeout') callbacks.onTimeout?.()
  }
  ws.onerror = () => callbacks.onError?.()
  ws.onclose = () => callbacks.onClose?.()
  return ws
}
