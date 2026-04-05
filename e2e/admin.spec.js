import { test, expect } from '@playwright/test'
import { ADMIN_KEY, cleanupMissions } from './helpers.js'

test.describe('Admin — Mission Builder', () => {
  test.beforeEach(async ({ request }) => {
    await cleanupMissions(request)
  })

  test.afterAll(async ({ request }) => {
    await cleanupMissions(request)
  })

  async function loginAdmin(page) {
    await page.goto('/admin')
    await page.fill('input[type="password"]', ADMIN_KEY)
    await page.click('text=ENTRER')
    await page.waitForURL('**/admin/dashboard')
  }

  test('refuse une mauvaise clé admin', async ({ page }) => {
    await page.goto('/admin')
    await page.fill('input[type="password"]', 'mauvaise-cle')
    await page.click('text=ENTRER')
    await expect(page.getByText(/Clé admin invalide/i)).toBeVisible()
    await expect(page).toHaveURL('/admin')
  })

  test('dashboard affiche message quand aucune mission', async ({ page }) => {
    await loginAdmin(page)
    await expect(page.getByText('Aucune mission créée')).toBeVisible()
  })

  test('navigue vers le mission builder', async ({ page }) => {
    await loginAdmin(page)
    await page.click('text=+ NOUVELLE MISSION')
    await expect(page).toHaveURL('**/admin/builder/new')
    await expect(page.getByText('MISSION BUILDER')).toBeVisible()
  })

  test('crée une mission complète via le builder', async ({ page }) => {
    await loginAdmin(page)
    await page.click('text=+ NOUVELLE MISSION')

    // Step 0 — Infos
    await page.fill('input[placeholder="Opération Tétreaultville"]', 'Test Mission Builder')
    await page.fill('textarea[placeholder*="agent X"]', 'Lore de test Playwright.')
    await page.fill('input[type="password"]', '9876')
    await page.fill('input[placeholder="45"]', '30')
    await page.fill('textarea[placeholder*="OMEGA-7"]', 'Récompense de test.')
    await page.click('text=SUIVANT')

    // Step 1 — Waypoints (un waypoint par défaut)
    await expect(page).toContainText('INFOS') // tabs toujours visibles
    await page.fill('input[placeholder="ex: Parc L.-O.-Taillon"]', 'Waypoint Test')
    // Lat/Lng manuels
    await page.fill('input[placeholder="45.5680"]', '45.5680')
    await page.fill('input[placeholder="-73.5490"]', '-73.5490')
    // Enigme — question + réponse
    await page.fill('textarea[placeholder*="Lattes"]', 'Question test?')
    await page.fill('input[placeholder="ex: 84"]', 'reponse-test')
    await page.click('text=SUIVANT')

    // Step 2 — Review
    await expect(page.getByText('Test Mission Builder')).toBeVisible()
    await expect(page.getByText('30 minutes')).toBeVisible()
    await expect(page.getByText('1')).toBeVisible() // nb waypoints
    await page.click('text=PUBLIER LA MISSION')

    // Redirige vers dashboard
    await page.waitForURL('**/admin/dashboard', { timeout: 10_000 })
    await expect(page.getByText('Test Mission Builder')).toBeVisible()
    await expect(page.getByText('ACTIVE')).toBeVisible()
  })

  test('supprime une mission depuis le dashboard', async ({ page, request }) => {
    // Seed directement via API
    const seed = await request.post('/api/admin/missions', {
      headers: { Authorization: `Bearer ${ADMIN_KEY}` },
      data: {
        title: 'Mission à supprimer',
        pin: '0000',
        duration_minutes: 10,
        waypoints: [],
      },
    })
    const mission = await seed.json()

    await loginAdmin(page)
    await expect(page.getByText('Mission à supprimer')).toBeVisible()

    // Click ✕ et confirmer
    page.on('dialog', (dialog) => dialog.accept())
    await page.click('button:has-text("✕")')

    // Mission disparaît
    await expect(page.getByText('Mission à supprimer')).not.toBeVisible({ timeout: 5000 })
  })

  test('logout retourne à l\'écran login admin', async ({ page }) => {
    await loginAdmin(page)
    await page.click('text=LOGOUT')
    await expect(page).toHaveURL('/admin')
    // Accès direct au dashboard redirige vers login
    await page.goto('/admin/dashboard')
    await expect(page).toHaveURL('/admin')
  })
})
