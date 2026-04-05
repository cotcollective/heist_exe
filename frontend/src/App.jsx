import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useMissionStore } from './store/missionStore'
import Boot          from './pages/Boot'
import Briefing      from './pages/Briefing'
import WaypointHunt  from './pages/WaypointHunt'
import Enigma        from './pages/Enigma'
import RewardUnlock  from './pages/RewardUnlock'
import AdminLogin     from './pages/admin/AdminLogin'
import AdminDashboard from './pages/admin/AdminDashboard'
import MissionBuilder from './pages/admin/MissionBuilder'

function PlayerRoute({ children }) {
  const token = useMissionStore((s) => s.token)
  if (!token) return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"         element={<Boot />} />
        <Route path="/briefing" element={<PlayerRoute><Briefing /></PlayerRoute>} />
        <Route path="/hunt"     element={<PlayerRoute><WaypointHunt /></PlayerRoute>} />
        <Route path="/enigma/:waypointId" element={<PlayerRoute><Enigma /></PlayerRoute>} />
        <Route path="/reward"   element={<PlayerRoute><RewardUnlock /></PlayerRoute>} />
        <Route path="/admin"                    element={<AdminLogin />} />
        <Route path="/admin/dashboard"          element={<AdminDashboard />} />
        <Route path="/admin/builder/new"        element={<MissionBuilder />} />
        <Route path="/admin/builder/:missionId" element={<MissionBuilder />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
