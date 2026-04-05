import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { adminApi } from '../../api/client'
import { HxInput, HxButton, HxCard, HxDivider, HxBadge } from '../../components/HxAtoms'
import WaypointEditor from '../../components/WaypointEditor'
import GlitchText from '../../components/GlitchText'

// ── Audio Recorder inline ─────────────────────────────────────────────────────
function AudioRecorder({ missionId, adminKey, existingFile, onUploaded }) {
  const [state, setState]       = useState('idle')
  const [duration, setDuration] = useState(0)
  const [error, setError]       = useState('')
  const mediaRef  = useRef(null)
  const chunksRef = useRef([])
  const timerRef  = useRef(null)

  const startRec = async () => {
    setError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const rec = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' })
      chunksRef.current = []
      rec.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        const file = new File([blob], `mission_audio_${Date.now()}.webm`, { type: 'audio/webm' })
        setState('uploading')
        try {
          const res = await adminApi.uploadAudio(adminKey, missionId, file)
          onUploaded?.(res.filename)
          setState('done')
        } catch (e) {
          setError(e.message)
          setState('error')
        }
      }
      rec.start()
      mediaRef.current = rec
      setState('recording')
      setDuration(0)
      timerRef.current = setInterval(() => setDuration((d) => d + 1), 1000)
    } catch {
      setError('Microphone inaccessible. Vérifie les permissions.')
      setState('error')
    }
  }

  const stopRec = () => {
    clearInterval(timerRef.current)
    mediaRef.current?.stop()
  }

  const uploadFile = async (e) => {
    const file = e.target.files?.[0]
    if (!file || !missionId) return
    setState('uploading')
    setError('')
    try {
      const res = await adminApi.uploadAudio(adminKey, missionId, file)
      onUploaded?.(res.filename)
      setState('done')
    } catch (err) {
      setError(err.message)
      setState('error')
    }
  }

  const fmt = (s) =>
    `${Math.floor(s / 60).toString().padStart(2,'0')}:${(s % 60).toString().padStart(2,'0')}`

  if (!missionId) return (
    <div className="text-hx-dim text-xs font-mono p-3 border border-hx-border rounded">
      // Sauvegarde la mission d'abord pour activer l'enregistrement audio.
    </div>
  )

  return (
    <div className="space-y-3">
      {existingFile && state !== 'done' && (
        <div className="flex items-center gap-2 text-xs font-mono text-hx-teal border border-hx-teal/30 bg-hx-teal/5 p-2 rounded">
          <span>♫</span>
          <span className="flex-1 truncate">{existingFile}</span>
          <HxBadge variant="teal">ACTIF</HxBadge>
        </div>
      )}
      {state === 'done' && (
        <div className="text-hx-green text-xs font-mono p-2 border border-hx-green/30 rounded">
          ✓ Audio uploadé avec succès.
        </div>
      )}
      {error && (
        <div className="text-hx-red text-xs font-mono p-2 border border-hx-red/30 rounded">
          // {error}
        </div>
      )}
      <div className="flex gap-2 flex-wrap">
        {(state === 'idle' || state === 'done' || state === 'error') && (
          <>
            <HxButton variant="amber" onClick={startRec} className="text-xs flex-1">
              ● ENREGISTRER
            </HxButton>
            <label className="flex-1 cursor-pointer">
              <input type="file" accept="audio/*" onChange={uploadFile} className="hidden" />
              <div className="hx-btn-ghost text-xs py-2 text-center rounded border border-hx-border font-mono hover:border-hx-dim transition-colors">
                ↑ UPLOADER
              </div>
            </label>
          </>
        )}
        {state === 'recording' && (
          <HxButton variant="danger" onClick={stopRec} className="text-xs flex-1 animate-pulse">
            ■ STOP  {fmt(duration)}
          </HxButton>
        )}
        {state === 'uploading' && (
          <div className="text-hx-sub text-xs font-mono animate-blink py-2">Upload en cours…</div>
        )}
      </div>
    </div>
  )
}

// ── Helpers ───────────────────────────────────────────────────────────────────
const newWaypoint = (order) => ({
  _id: `wp_${Date.now()}_${Math.random().toString(36).slice(2)}`,
  order,
  title: '',
  hint: '',
  lat: null,
  lng: null,
  radius_meters: 30,
  qr_code: null,
  enigma: { question: '', answer: '', hint: '' },
})

// ── MissionBuilder ────────────────────────────────────────────────────────────
export default function MissionBuilder() {
  const { id }   = useParams()
  const navigate = useNavigate()
  const isNew    = !id || id === 'new'
  const adminKey = sessionStorage.getItem('hx_admin_key') ?? ''

  const [form, setForm]           = useState({
    title: '', lore: '', pin: '', duration_minutes: 45, reward_text: '', audio_file: null,
  })
  const [waypoints, setWaypoints] = useState([newWaypoint(0)])
  const [savedId, setSavedId]     = useState(isNew ? null : parseInt(id))
  const [saving, setSaving]       = useState(false)
  const [saved, setSaved]         = useState(false)
  const [error, setError]         = useState('')
  const [loading, setLoading]     = useState(!isNew)

  useEffect(() => {
    if (isNew) return
    adminApi.listMissions(adminKey).then((missions) => {
      const m = missions.find((x) => x.id === parseInt(id))
      if (!m) { navigate('/admin/dashboard'); return }
      setForm({
        title: m.title, lore: m.lore ?? '', pin: '',
        duration_minutes: m.duration_minutes,
        reward_text: m.reward_text ?? '', audio_file: m.audio_file,
      })
      setWaypoints((m.waypoints ?? []).map((wp, i) => ({
        _id: `wp_loaded_${wp.id}`, order: i,
        title: wp.title, hint: wp.hint ?? '',
        lat: wp.lat, lng: wp.lng, radius_meters: wp.radius_meters,
        qr_code: wp.qr_code,
        enigma: wp.enigma
          ? { question: wp.enigma.question, answer: '', hint: wp.enigma.hint ?? '' }
          : null,
      })))
    }).catch(() => navigate('/admin/dashboard'))
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line

  const upd = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const addWaypoint = () =>
    setWaypoints((wps) => [...wps, newWaypoint(wps.length)])

  const updateWaypoint = useCallback((index, wp) =>
    setWaypoints((wps) => wps.map((w, i) => i === index ? wp : w)), [])

  const removeWaypoint = (index) =>
    setWaypoints((wps) => wps.filter((_, i) => i !== index).map((w, i) => ({ ...w, order: i })))

  const moveWp = (index, dir) =>
    setWaypoints((wps) => {
      const next = [...wps]
      const target = index + dir
      if (target < 0 || target >= next.length) return wps
      ;[next[index], next[target]] = [next[target], next[index]]
      return next.map((w, i) => ({ ...w, order: i }))
    })

  const validate = () => {
    if (!form.title.trim()) return 'Titre requis.'
    if (isNew && form.pin.trim().length < 4) return 'PIN minimum 4 caractères.'
    if (form.duration_minutes < 5) return 'Durée minimum 5 minutes.'
    for (const [i, wp] of waypoints.entries()) {
      if (!wp.title.trim()) return `WP${i}: titre requis.`
      if (!wp.lat || !wp.lng) return `WP${i} "${wp.title}": position GPS requise.`
      if (wp.enigma && !wp.enigma.question.trim()) return `WP${i}: question requise.`
      if (wp.enigma && !wp.enigma.answer.trim()) return `WP${i}: réponse requise.`
    }
    return null
  }

  const handleSave = async () => {
    const err = validate()
    if (err) { setError(err); return }
    setError(''); setSaving(true)
    try {
      const payload = {
        title: form.title.trim(),
        lore: form.lore.trim() || null,
        pin: form.pin.trim() || (isNew ? '2077' : '____'),
        duration_minutes: parseInt(form.duration_minutes),
        reward_text: form.reward_text.trim() || null,
        waypoints: waypoints.map((wp, i) => ({
          order: i,
          title: wp.title.trim(),
          hint: wp.hint?.trim() || null,
          lat: parseFloat(wp.lat),
          lng: parseFloat(wp.lng),
          radius_meters: parseInt(wp.radius_meters) || 30,
          qr_code: wp.qr_code || null,
          enigma: wp.enigma?.question && wp.enigma?.answer
            ? { question: wp.enigma.question.trim(), answer: wp.enigma.answer.trim(), hint: wp.enigma.hint?.trim() || null }
            : null,
        })),
      }
      if (!isNew && savedId) await adminApi.deleteMission(adminKey, savedId)
      const mission = await adminApi.createMission(adminKey, payload)
      setSavedId(mission.id)
      setForm((f) => ({ ...f, audio_file: mission.audio_file }))
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return (
    <div className="hx-screen flex items-center justify-center">
      <div className="font-mono text-hx-sub text-xs animate-blink">Chargement…</div>
    </div>
  )

  return (
    <div className="hx-screen flex flex-col">
      {/* Header */}
      <div className="px-4 pt-safe pb-3 border-b border-hx-border flex items-center justify-between shrink-0">
        <div>
          <div className="text-hx-amber text-[10px] tracking-widest font-mono mb-0.5">
            {isNew ? '// NOUVELLE MISSION' : `// ÉDITION — ID ${savedId}`}
          </div>
          <GlitchText
            text={isNew ? 'MISSION BUILDER' : (form.title.toUpperCase() || 'MISSION BUILDER')}
            autoPlay className="text-lg font-bold text-hx-text"
          />
        </div>
        <button onClick={() => navigate('/admin/dashboard')}
          className="text-hx-dim text-xs font-mono hover:text-hx-text transition-colors">
          ← BACK
        </button>
      </div>

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto px-4 py-5 space-y-6 pb-36">

        {/* Mission info */}
        <section className="space-y-4">
          <div className="text-[10px] text-hx-sub font-mono tracking-widest">// MISSION INFO</div>
          <HxInput label="TITRE" required value={form.title} onChange={upd('title')}
            placeholder="ex: Opération Tétreaultville" />
          <HxInput label="LORE — CONTEXTE NARRATIF" value={form.lore} onChange={upd('lore')}
            placeholder="L'agent X a été compromis…" rows={4}
            hint="Affiché dans l'écran Briefing avant le départ." />
          <div className="grid grid-cols-2 gap-3">
            <HxInput label={isNew ? 'PIN ACCÈS *' : 'NOUVEAU PIN (vide = inchangé)'}
              value={form.pin} onChange={upd('pin')} placeholder="ex: 2077"
              inputMode="numeric" maxLength={10} hint="Min. 4 caractères." />
            <HxInput label="DURÉE (minutes)" type="number"
              value={form.duration_minutes} onChange={upd('duration_minutes')} />
          </div>
          <HxInput label="RÉCOMPENSE FINALE" value={form.reward_text} onChange={upd('reward_text')}
            placeholder="15$ au comptoir, identifie-toi avec OMEGA-7…" rows={2}
            hint="Affiché sur l'écran ACCÈS ACCORDÉ." />
        </section>

        {/* Audio */}
        <section className="space-y-3">
          <div className="text-[10px] text-hx-sub font-mono tracking-widest">// MESSAGE AUDIO CRYPTÉ</div>
          <p className="text-hx-dim text-xs font-sans leading-relaxed">
            Ce message joue automatiquement dans le Briefing. Enregistre directement ou uploade un fichier.
          </p>
          <AudioRecorder missionId={savedId} adminKey={adminKey}
            existingFile={form.audio_file}
            onUploaded={(fn) => setForm((f) => ({ ...f, audio_file: fn }))} />
        </section>

        {/* Waypoints */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-[10px] text-hx-sub font-mono tracking-widest">
              // WAYPOINTS — {waypoints.length} étape{waypoints.length > 1 ? 's' : ''}
            </div>
            <HxBadge variant="teal">{waypoints.length} WP</HxBadge>
          </div>
          <p className="text-hx-dim text-xs font-sans leading-relaxed">
            Clique sur la map pour placer chaque waypoint. Dernier = planque finale{' '}
            <span className="text-hx-teal font-mono">(sans énigme)</span>.
          </p>
          <div className="space-y-2">
            {waypoints.map((wp, i) => (
              <WaypointEditor
                key={wp._id}
                waypoint={wp} index={i}
                onUpdate={(updated) => updateWaypoint(i, updated)}
                onRemove={() => removeWaypoint(i)}
                onMoveUp={() => moveWp(i, -1)}
                onMoveDown={() => moveWp(i, 1)}
                isFirst={i === 0}
                isLast={i === waypoints.length - 1}
              />
            ))}
          </div>
          <HxButton variant="ghost" onClick={addWaypoint} className="w-full text-xs py-2">
            + AJOUTER UN WAYPOINT
          </HxButton>
        </section>

        {/* Preview */}
        <section>
          <HxDivider label="PREVIEW PAYLOAD" />
          <div className="bg-hx-surface border border-hx-border rounded p-3 font-mono text-[10px] text-hx-dim overflow-x-auto whitespace-pre leading-relaxed">
{`{
  "title":    "${form.title || '…'}",
  "pin":      "${form.pin ? '****' : '(défaut: 2077)'}",
  "duration": ${form.duration_minutes} min,
  "waypoints": ${waypoints.length} × [${waypoints.map(w => w.enigma ? 'énigme' : 'final').join(', ')}],
  "audio":    ${form.audio_file ? '"' + form.audio_file + '"' : 'null'}
}`}
          </div>
        </section>
      </div>

      {/* Footer sticky */}
      <div className="absolute bottom-0 left-0 right-0 max-w-[480px] mx-auto border-t border-hx-border bg-hx-bg px-4 py-4 space-y-2">
        {error && (
          <div className="text-hx-red text-xs font-mono bg-hx-red/5 border border-hx-red/30 p-2 rounded">
            // {error}
          </div>
        )}
        {saved && (
          <div className="text-hx-green text-xs font-mono text-center animate-pulse">
            ✓ Mission sauvegardée — ID {savedId}
          </div>
        )}
        <div className="flex gap-2">
          <HxButton variant="ghost" onClick={() => navigate('/admin/dashboard')} className="flex-1">
            ANNULER
          </HxButton>
          <HxButton onClick={handleSave} loading={saving} className="flex-1 py-3">
            {saving ? 'SAUVEGARDE…' : savedId ? '✓ METTRE À JOUR' : '✓ CRÉER MISSION'}
          </HxButton>
        </div>
      </div>
    </div>
  )
}
