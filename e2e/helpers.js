/**
 * Helpers E2E HEIST.EXE
 * Seed une mission de test via API et retourne les infos nécessaires.
 */

export const ADMIN_KEY   = process.env.ADMIN_KEY   ?? 'admin-dev-2077'
export const API_BASE    = process.env.BASE_URL     ?? 'http://localhost'
export const PLAYER_NAME = 'Agent_Playwright'

export const TEST_MISSION = {
  title:            'Mission E2E',
  lore:             'Test automatisé Playwright.',
  pin:              '1337',
  duration_minutes: 45,
  reward_text:      'Tu as réussi le test E2E. Bien joué.',
  waypoints: [
    {
      order: 0,
      title: 'Point Alpha',
      hint:  'Premier waypoint de test',
      lat:    45.5680,
      lng:   -73.5490,
      radius_meters: 9999, // Grand rayon — toujours "en portée" en test
      enigma: {
        question: 'Quelle est la réponse à tout?',
        answer:   '42',
        hint:     'Douglas Adams.',
      },
    },
    {
      order: 1,
      title: 'Point Oméga',
      hint:  'Dernier waypoint',
      lat:    45.5695,
      lng:   -73.5475,
      radius_meters: 9999,
      enigma: {
        question: 'Combien font 6 × 7?',
        answer:   '42',
      },
    },
    {
      order: 2,
      title: 'Extraction',
      hint:  'Mission terminée.',
      lat:    45.5702,
      lng:   -73.5460,
      radius_meters: 9999,
      enigma: null,
    },
  ],
}

/**
 * Crée une mission de test via API REST directement.
 * Retourne l'objet mission créé.
 */
export async function seedMission(request) {
  const res = await request.post(`${API_BASE}/api/admin/missions`, {
    headers: { Authorization: `Bearer ${ADMIN_KEY}` },
    data: TEST_MISSION,
  })
  if (!res.ok()) {
    throw new Error(`Seed mission failed: ${res.status()} — ${await res.text()}`)
  }
  return res.json()
}

/**
 * Supprime toutes les missions de test (nettoyage).
 */
export async function cleanupMissions(request) {
  const res  = await request.get(`${API_BASE}/api/admin/missions`, {
    headers: { Authorization: `Bearer ${ADMIN_KEY}` },
  })
  if (!res.ok()) return
  const missions = await res.json()
  for (const m of missions) {
    await request.delete(`${API_BASE}/api/admin/missions/${m.id}`, {
      headers: { Authorization: `Bearer ${ADMIN_KEY}` },
    })
  }
}

/**
 * Auth joueur via UI — remplit PIN + player name + soumet.
 */
export async function loginAsPlayer(page, missionId, pin = '1337', name = PLAYER_NAME) {
  await page.goto('/')
  // Attendre que la liste de missions charge
  await page.waitForSelector('[data-testid="mission-card"]', { timeout: 10_000 })

  // Cliquer sur la mission
  await page.click(`[data-testid="mission-card-${missionId}"]`)

  // Remplir les champs
  await page.fill('[data-testid="player-name"]', name)
  await page.fill('[data-testid="pin-input"]', pin)
  await page.click('[data-testid="submit-auth"]')

  // Attendre la redirection vers briefing
  await page.waitForURL('**/briefing', { timeout: 8_000 })
}
