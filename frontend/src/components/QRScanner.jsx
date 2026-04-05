import { useEffect, useRef, useState } from 'react'
import { Html5QrcodeScanner, Html5QrcodeScanType } from 'html5-qrcode'

let _idCounter = 0

export default function QRScanner({ onResult, onClose, label = 'Scanner le QR code' }) {
  const [error, setError]     = useState('')
  const [active, setActive]   = useState(true)
  const scannerRef = useRef(null)
  const divId      = useRef(`qr-scanner-${++_idCounter}`)

  useEffect(() => {
    if (!active) return

    const scanner = new Html5QrcodeScanner(
      divId.current,
      {
        fps: 10,
        qrbox: { width: 240, height: 240 },
        supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA],
        showTorchButtonIfSupported: true,
        showZoomSliderIfSupported: false,
        defaultZoomValueIfSupported: 1,
      },
      false,
    )

    scanner.render(
      (decoded) => {
        scanner.clear().catch(() => {})
        setActive(false)
        onResult?.(decoded)
      },
      (err) => {
        // Erreurs silencieuses (frame sans QR) — on log seulement les vraies
        if (!err.includes('No QR code')) {
          setError('Caméra inaccessible. Vérifie les permissions.')
        }
      },
    )

    scannerRef.current = scanner
    return () => { scanner.clear().catch(() => {}) }
  }, [active]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="bg-hx-surface border border-hx-border rounded overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-hx-border">
        <span className="text-hx-sub text-xs tracking-widest font-mono">{label}</span>
        <button
          onClick={onClose}
          className="text-hx-dim hover:text-hx-text text-sm font-mono transition-colors"
        >
          ✕
        </button>
      </div>

      {/* Viewfinder */}
      <div className="relative">
        <div id={divId.current} className="qr-viewfinder" />
        {/* Overlay corners cyberpunk */}
        <div className="absolute inset-4 pointer-events-none">
          <div className="absolute top-0 left-0 w-6 h-6 border-t-2 border-l-2 border-hx-teal" />
          <div className="absolute top-0 right-0 w-6 h-6 border-t-2 border-r-2 border-hx-teal" />
          <div className="absolute bottom-0 left-0 w-6 h-6 border-b-2 border-l-2 border-hx-teal" />
          <div className="absolute bottom-0 right-0 w-6 h-6 border-b-2 border-r-2 border-hx-teal" />
        </div>
      </div>

      {error && (
        <div className="px-3 py-2 text-hx-red text-xs font-mono border-t border-hx-border">
          // {error}
        </div>
      )}
    </div>
  )
}
