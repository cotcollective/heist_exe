import { test, expect } from '@playwright/test'
import { seedMission, cleanupMissions } from './helpers.js'

test.describe('Game loop — progression mission complète', () => {
  let mission

  test.beforeAll(async ({ request }) => {
    await cleanupMissions(request)
    mission = await seedMission(request)
  })

  test.afterAll(async ({ request }) => {
    await cleanupMissions(request)
  })

  // Helper interne — auth + aller au hunt
  async function startMission(page) {
    await page.goto('/')
    await page.click('text=Mission E2E')
    await page.fill('[placeholder="••••"]', '1337')
    await page.click('text=ENTRER')
    await page.waitForURL('**/briefing')
    await page.click('text=DÉMARRER LA MISSION')
    await page.waitForURL('**/hunt')
  }

  test('affiche la map OSM et le premier waypoint', async ({ page }) => {
    await startMission(page)
    // Map Leaflet chargée
    await expect(page.locator('.leaflet-container')).toBeVisible()
    // Titre du waypoint
    await expect(page.getByText('POINT ALPHA')).toBeVisible()
    // Distance affichée (peu importe la valeur avec le grand radius)
    await expect(page.locator('text=/\\d+m/')).toBeVisible()
  })

  test('détecte la zone GPS et active le bouton d\'énigme', async ({ page }) => {
    // La géoloc mock est dans la zone (radius 9999m) → bouton actif
    await startMission(page)
    // Attendre que le GPS se stabilise
    await page.waitForTimeout(2000)
    const btn = page.locator('button', { hasText: /ACCÉDER|ÉNIGME/ })
    await expect(btn).not.toBeDisabled({ timeout: 5000 })
  })

  test('accède à l\'énigme et affiche la question', async ({ page }) => {
    await startMission(page)
    await page.waitForTimeout(1500)
    await page.click('button:has-text("ACCÉDER")')
    await page.waitForURL(/\/enigma\/\d+/)
    await expect(page.getByText(/Quelle est la réponse à tout/)).toBeVisible()
    await expect(page.getByText(/Douglas Adams/)).toBeVisible() // hint
  })

  test('rejette une mauvaise réponse', async ({ page }) => {
    await startMission(page)
    await page.waitForTimeout(1500)
    await page.click('button:has-text("ACCÉDER")')
    await page.waitForURL(/\/enigma\/\d+/)
    await page.fill('input[placeholder="Entrer la réponse…"]', '99')
    await page.click('text=SOUMETTRE')
    await expect(page.getByText(/Code incorrect/i)).toBeVisible()
    // Reste sur l'énigme
    await expect(page).toHaveURL(/\/enigma\//)
  })

  test('valide la bonne réponse et affiche ACCÈS ACCORDÉ', async ({ page }) => {
    await startMission(page)
    await page.waitForTimeout(1500)
    await page.click('button:has-text("ACCÉDER")')
    await page.waitForURL(/\/enigma\/\d+/)
    await page.fill('input[placeholder="Entrer la réponse…"]', '42')
    await page.click('text=SOUMETTRE')
    await expect(page.getByText('ACCÈS ACCORDÉ')).toBeVisible({ timeout: 5000 })
  })

  test('avance au waypoint suivant après bonne réponse', async ({ page }) => {
    await startMission(page)
    await page.waitForTimeout(1500)
    // WP0
    await page.click('button:has-text("ACCÉDER")')
    await page.waitForURL(/\/enigma\/\d+/)
    await page.fill('input[placeholder="Entrer la réponse…"]', '42')
    await page.click('text=SOUMETTRE')
    // Retour hunt
    await page.waitForURL('**/hunt', { timeout: 5000 })
    // WP1 maintenant
    await expect(page.getByText('POINT OMÉGA')).toBeVisible()
  })

  test('game loop complet — 3 waypoints → MISSION ACCOMPLIE', async ({ page }) => {
    await startMission(page)
    await page.waitForTimeout(1500)

    // WP0 — "42"
    await page.click('button:has-text("ACCÉDER")')
    await page.waitForURL(/\/enigma\/\d+/)
    await page.fill('input[placeholder="Entrer la réponse…"]', '42')
    await page.click('text=SOUMETTRE')
    await page.waitForURL('**/hunt', { timeout: 6000 })
    await page.waitForTimeout(1000)

    // WP1 — "42" aussi (6×7)
    await page.click('button:has-text("ACCÉDER")')
    await page.waitForURL(/\/enigma\/\d+/)
    await page.fill('input[placeholder="Entrer la réponse…"]', '42')
    await page.click('text=SOUMETTRE')
    await page.waitForURL('**/hunt', { timeout: 6000 })
    await page.waitForTimeout(1000)

    // WP2 — pas d'énigme, bouton "ACCÉDER" toujours présent
    // mais pointe vers reward directement
    await expect(page.getByText('EXTRACTION')).toBeVisible()
    // Un clic sur accéder redirige vers reward (pas d'énigme)
    await page.click('button:has-text("ACCÉDER")')
    await page.waitForURL('**/reward', { timeout: 6000 })

    await expect(page.getByText('MISSION ACCOMPLIE')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText(/OMEGA-7|15\$/)).toBeVisible()
  })

  test('← CARTE depuis l\'énigme retourne sur la map', async ({ page }) => {
    await startMission(page)
    await page.waitForTimeout(1500)
    await page.click('button:has-text("ACCÉDER")')
    await page.waitForURL(/\/enigma\//)
    await page.click('text=← CARTE')
    await expect(page).toHaveURL(/\/hunt/)
  })
})
