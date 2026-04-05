import { useState, useEffect, useRef } from 'react'
import { Howl } from 'howler'

export default function AudioPlayer({ src, autoPlay = false, label = 'MESSAGE CRYPTÉ' }) {
  const [state, setState] = useState('idle') // idle | loading | playing | paused | done | error
  const [progress, setProgress] = useState(0)
  const soundRef = useRef(null)
  const rafRef   = useRef(null)

  useEffect(() => {
    if (!src) return
    setState('loading')
    const sound = new Howl({
      src: [src],
      html5: true,
      onload:  () => setState('idle'),
      onplay:  () => {
        setState('playing')
        const tick = () => {
          if (!soundRef.current) return
          const dur = soundRef.current.duration()
          const seek = soundRef.current.seek()
          setProgress(dur > 0 ? (seek / dur) * 100 : 0)
          rafRef.current = requestAnimationFrame(tick)
        }
        rafRef.current = requestAnimationFrame(tick)
      },
      onpause: () => { setState('paused'); cancelAnimationFrame(rafRef.current) },
      onend:   () => { setState('done');  cancelAnimationFrame(rafRef.current); setProgress(100) },
      onloaderror: () => setState('error'),
    })
    soundRef.current = sound
    if (autoPlay) sound.play()
    return () => { cancelAnimationFrame(rafRef.current); sound.unload() }
  }, [src]) // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = () => {
    if (!soundRef.current) return
    if (state === 'playing') soundRef.current.pause()
    else soundRef.current.play()
  }

  const icons = {
    idle:    '▶',
    loading: '…',
    playing: '⏸',
    paused:  '▶',
    done:    '↺',
    error:   '✕',
  }

  return (
    <div className="bg-hx-surface border border-hx-border rounded p-4 font-mono">
      <div className="flex items-center gap-3">
        <button
          onClick={toggle}
          disabled={state === 'loading' || state === 'error'}
          className="w-10 h-10 flex items-center justify-center bg-hx-muted border border-hx-border
                     rounded text-hx-teal hover:border-hx-teal transition-colors disabled:opacity-40"
        >
          {icons[state]}
        </button>

        <div className="flex-1">
          <div className="text-xs text-hx-sub tracking-widest mb-2">{label}</div>
          <div className="h-1 bg-hx-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-hx-teal transition-all duration-300 rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {state === 'playing' && (
          <div className="flex gap-px items-end h-5">
            {[3,5,4,6,3,5,4].map((h, i) => (
              <div
                key={i}
                className="w-1 bg-hx-teal rounded-sm"
                style={{
                  height: `${h * 3}px`,
                  animation: `equalizer ${0.4 + i * 0.07}s ease-in-out infinite alternate`,
                }}
              />
            ))}
          </div>
        )}
      </div>

      {state === 'error' && (
        <p className="text-hx-red text-xs mt-2">// Erreur chargement audio</p>
      )}
    </div>
  )
}
