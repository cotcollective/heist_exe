import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useMissionStore } from './store/missionStore'
import Boot          from './pages/Boot'
import Start         from './pages/Start'
import Briefing      from './pages/Briefing'
import WaypointHunt  from './pages/WaypointHunt'
import Enigma        from './pages/Enigma'
import RewardUnlock  from './pages/RewardUnlock'
import WorldMap      from './pages/WorldMap'
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
        {/* Nouvelle partie : aucun compte, un jeton, on joue. */}
        <Route path="/start"    element={<Start />} />
        <Route path="/briefing" element={<PlayerRoute><Briefing /></PlayerRoute>} />
        <Route path="/hunt"     element={<PlayerRoute><WaypointHunt /></PlayerRoute>} />
        <Route path="/enigma/:waypointId" element={<PlayerRoute><Enigma /></PlayerRoute>} />
        <Route path="/reward"   element={<PlayerRoute><RewardUnlock /></PlayerRoute>} />
        {/* Le monde est public : pas de mission requise pour le consulter. */}
        <Route path="/world"    element={<WorldMap />} />
        <Route path="/admin"                    element={<AdminLogin />} />
        <Route path="/admin/dashboard"          element={<AdminDashboard />} />
        <Route path="/admin/builder/new"        element={<MissionBuilder />} />
        <Route path="/admin/builder/:missionId" element={<MissionBuilder />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
