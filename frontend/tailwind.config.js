/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        hx: {
          bg:       '#0a0a0a',
          surface:  '#111111',
          border:   '#1f1f1f',
          muted:    '#2a2a2a',
          dim:      '#555555',
          text:     '#e8e8e8',
          sub:      '#888888',
          teal:     '#00d4aa',
          'teal-d': '#009977',
          purple:   '#a78bfa',
          amber:    '#f59e0b',
          red:      '#ef4444',
          green:    '#22c55e',
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', '"Cascadia Code"', 'monospace'],
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
      },
      animation: {
        'blink': 'blink 1s step-end infinite',
        'scanline': 'scanline 8s linear infinite',
        'glitch': 'glitch 0.3s steps(2) infinite',
        'flicker': 'flicker 4s linear infinite',
        'pulse-teal': 'pulse-teal 2s ease-in-out infinite',
        'countdown-warn': 'countdown-warn 0.5s ease-in-out infinite',
      },
      keyframes: {
        blink: { '0%,100%': { opacity: '1' }, '50%': { opacity: '0' } },
        scanline: {
          '0%':   { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        glitch: {
          '0%':  { clipPath: 'inset(20% 0 50% 0)', transform: 'translate(-2px, 0)' },
          '50%': { clipPath: 'inset(60% 0 10% 0)', transform: 'translate(2px, 0)' },
          '100%':{ clipPath: 'inset(40% 0 30% 0)', transform: 'translate(0, 0)' },
        },
        flicker: {
          '0%,95%,100%': { opacity: '1' },
          '96%':         { opacity: '0.7' },
          '98%':         { opacity: '0.9' },
        },
        'pulse-teal': {
          '0%,100%': { boxShadow: '0 0 0 0 rgba(0,212,170,0)' },
          '50%':     { boxShadow: '0 0 0 6px rgba(0,212,170,0.1)' },
        },
        'countdown-warn': {
          '0%,100%': { color: '#ef4444' },
          '50%':     { color: '#f59e0b' },
        },
      },
    },
  },
  plugins: [],
}
