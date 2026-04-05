import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useMissionStore = create(
  persist(
    (set, get) => ({
      // Auth
      token: null,
      mission: null,
      sessionId: null,
      playerName: 'Agent',

      // Progression
      currentWaypoint: null,
      completedWaypoints: [],
      missionComplete: false,

      // Timer
      startedAt: null,
      remainingSeconds: null,

      // Actions
      setAuth: (token, mission, sessionId, playerName) => set({
        token,
        mission,
        sessionId,
        playerName,
        currentWaypoint: mission?.waypoints?.[0] ?? null,
        completedWaypoints: [],
        missionComplete: false,
        startedAt: Date.now(),
        remainingSeconds: (mission?.duration_minutes ?? 45) * 60,
      }),

      setCurrentWaypoint: (wp) => set({ currentWaypoint: wp }),

      markWaypointDone: (wpId) => set((s) => ({
        completedWaypoints: [...s.completedWaypoints, wpId],
      })),

      advanceToWaypoint: (nextWp) => set((s) => ({
        completedWaypoints: s.currentWaypoint
          ? [...s.completedWaypoints, s.currentWaypoint.id]
          : s.completedWaypoints,
        currentWaypoint: nextWp ?? null,
      })),

      setMissionComplete: () => set({ missionComplete: true }),

      tickTimer: () => set((s) => ({
        remainingSeconds: Math.max(0, (s.remainingSeconds ?? 0) - 1),
      })),

      reset: () => set({
        token: null, mission: null, sessionId: null,
        playerName: 'Agent', currentWaypoint: null,
        completedWaypoints: [], missionComplete: false,
        startedAt: null, remainingSeconds: null,
      }),
    }),
    {
      name: 'heist-session',
      partialize: (s) => ({
        token: s.token,
        mission: s.mission,
        sessionId: s.sessionId,
        playerName: s.playerName,
        currentWaypoint: s.currentWaypoint,
        completedWaypoints: s.completedWaypoints,
        startedAt: s.startedAt,
        remainingSeconds: s.remainingSeconds,
      }),
    }
  )
)
