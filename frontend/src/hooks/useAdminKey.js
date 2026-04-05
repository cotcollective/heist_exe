import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export function useAdminKey() {
  const navigate = useNavigate()
  const key = sessionStorage.getItem('hx_admin_key')
  useEffect(() => {
    if (!key) navigate('/admin')
  }, []) // eslint-disable-line
  return key ?? ''
}
