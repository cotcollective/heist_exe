import { useState, useEffect } from 'react'

const CHARS = '!<>-_\\/[]{}—=+*^?#@$%&'

function scramble(text, progress) {
  return text
    .split('')
    .map((char, i) => {
      if (char === ' ') return ' '
      if (i < progress * text.length) return char
      return CHARS[Math.floor(Math.random() * CHARS.length)]
    })
    .join('')
}

export default function GlitchText({
  text,
  className = '',
  tag: Tag = 'span',
  autoPlay = false,
  duration = 800,
}) {
  const [display, setDisplay] = useState(autoPlay ? scramble(text, 0) : text)
  const [running, setRunning] = useState(false)

  const play = () => {
    if (running) return
    setRunning(true)
    const start = performance.now()
    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1)
      setDisplay(scramble(text, progress))
      if (progress < 1) requestAnimationFrame(tick)
      else { setDisplay(text); setRunning(false) }
    }
    requestAnimationFrame(tick)
  }

  useEffect(() => {
    if (autoPlay) {
      const t = setTimeout(play, 200)
      return () => clearTimeout(t)
    }
  }, [text]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Tag
      className={`font-mono select-none cursor-default ${className}`}
      onMouseEnter={!autoPlay ? play : undefined}
    >
      {display}
    </Tag>
  )
}
