// ── HxInput ───────────────────────────────────────────────────────────────────
export function HxInput({
  label, value, onChange, placeholder = '', type = 'text',
  hint, error, required, className = '', inputMode, maxLength, rows,
  ...props
}) {
  const Tag = rows ? 'textarea' : 'input'
  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      {label && (
        <label className="text-[10px] tracking-widest text-hx-sub font-mono">
          {label}{required && <span className="text-hx-red ml-1">*</span>}
        </label>
      )}
      <Tag
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        inputMode={inputMode}
        maxLength={maxLength}
        rows={rows ?? undefined}
        className={`hx-input resize-none ${error ? 'border-hx-red' : ''}`}
        {...props}
      />
      {hint && !error && <p className="text-[11px] text-hx-dim font-mono">{hint}</p>}
      {error && <p className="text-[11px] text-hx-red font-mono">// {error}</p>}
    </div>
  )
}

// ── HxButton ─────────────────────────────────────────────────────────────────
export function HxButton({
  children, onClick, variant = 'primary', disabled = false,
  className = '', type = 'button', loading = false,
}) {
  const base = 'font-mono text-sm py-2 px-4 rounded transition-all disabled:opacity-40 disabled:cursor-not-allowed'
  const variants = {
    primary: 'bg-hx-teal text-hx-bg font-bold hover:bg-hx-teal-d active:scale-95',
    ghost:   'bg-transparent text-hx-sub border border-hx-border hover:text-hx-text hover:border-hx-dim',
    danger:  'bg-transparent text-hx-red border border-hx-red/40 hover:bg-hx-red/10',
    amber:   'bg-transparent text-hx-amber border border-hx-amber/40 hover:bg-hx-amber/10',
  }
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`${base} ${variants[variant]} ${className}`}
    >
      {loading ? '…' : children}
    </button>
  )
}

// ── HxCard ────────────────────────────────────────────────────────────────────
export function HxCard({ children, className = '', onClick }) {
  return (
    <div
      onClick={onClick}
      className={`bg-hx-surface border border-hx-border rounded p-4 ${
        onClick ? 'cursor-pointer hover:border-hx-teal transition-colors' : ''
      } ${className}`}
    >
      {children}
    </div>
  )
}

// ── HxBadge ───────────────────────────────────────────────────────────────────
export function HxBadge({ children, variant = 'default' }) {
  const variants = {
    default: 'text-hx-sub border-hx-border',
    teal:    'text-hx-teal border-hx-teal/40',
    amber:   'text-hx-amber border-hx-amber/40',
    red:     'text-hx-red border-hx-red/40',
    green:   'text-hx-green border-hx-green/40',
  }
  return (
    <span className={`text-[10px] font-mono tracking-widest border px-2 py-0.5 rounded ${variants[variant]}`}>
      {children}
    </span>
  )
}

// ── HxDivider ────────────────────────────────────────────────────────────────
export function HxDivider({ label }) {
  return (
    <div className="flex items-center gap-3 my-4">
      <div className="flex-1 h-px bg-hx-border" />
      {label && <span className="text-[10px] text-hx-dim font-mono tracking-widest">{label}</span>}
      <div className="flex-1 h-px bg-hx-border" />
    </div>
  )
}
