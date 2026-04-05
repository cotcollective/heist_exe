import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { adminApi } from '../../api/client'
import GlitchText from '../../components/GlitchText'
import { HxInput, HxButton } from '../../components/HxAtoms'

export default function AdminLogin() {
  const navigate = useNavigate()
  const [key, setKey]   = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e) => {
    e.preventDefault()
    if (!key.trim()) return
    setLoading(true)
    setError('')
    try {
      await adminApi.listMissions(key)
      sessionStorage.setItem('hx_admin_key', key)
      navigate('/admin/dashboard')
    } catch {
      setError('Clé admin invalide.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="hx-screen flex flex-col p-6 pt-safe justify-center">
      <div className="mb-10">
        <div className="text-hx-amber text-xs tracking-widest mb-2">// ACCÈS COORDINATEUR</div>
        <GlitchText text="ADMIN.EXE" tag="h1" autoPlay className="text-4xl font-bold text-hx-text" />
        <div className="text-hx-sub text-xs mt-1">Mission builder — accès restreint</div>
      </div>

      <form onSubmit={handleLogin} className="flex flex-col gap-5">
        <HxInput
          label="CLÉ ADMIN"
          type="password"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          placeholder="••••••••"
          required
          hint="Définie dans ton .env — ADMIN_KEY"
        />
        {error && (
          <div className="text-hx-red text-xs font-mono border border-hx-red/30 bg-hx-red/5 p-3 rounded">
            // {error}
          </div>
        )}
        <HxButton type="submit" loading={loading} className="w-full py-3">
          ENTRER ▶
        </HxButton>
        <HxButton variant="ghost" onClick={() => navigate('/')} className="w-full">
          ← RETOUR JOUEUR
        </HxButton>
      </form>
    </div>
  )
}
