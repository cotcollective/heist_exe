import { test, expect } from '@playwright/test'
import { seedMission, cleanupMissions, loginAsPlayer } from './helpers.js'

test.describe('Boot — authentification joueur', () => {
  let mission

  test.beforeAll(async ({ request }) => {
    await cleanupMissions(request)
    mission = await seedMission(request)
  })

  test.afterAll(async ({ request }) => {
    await cleanupMissions(request)
  })

  test('affiche la liste des missions actives', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('HEIST.EXE')).toBeVisible()
    await expect(page.getByText('Mission E2E')).toBeVisible()
  })

  test('affiche la durée et les waypoints de la mission', async ({ page }) => {
    await page.goto('/')
    await page.click(`text=Mission E2E`)
    await expect(page.getByText('45 min')).toBeVisible()
    await expect(page.getByText('3 waypoints')).toBeVisible()
  })

  test('refuse un PIN incorrect', async ({ page }) => {
    await page.goto('/')
    await page.click('text=Mission E2E')
    await page.fill('[placeholder="••••"]', '9999')
    await page.click('text=ENTRER')
    await expect(page.getByText(/ACCÈS REFUSÉ|PIN incorrect/i)).toBeVisible()
    // Reste sur la page Boot
    await expect(page).toHaveURL('/')
  })

  test('authentifie avec le bon PIN et redirige vers briefing', async ({ page }) => {
    await page.goto('/')
    await page.click('text=Mission E2E')
    await page.fill('input[placeholder*="Agent"]', 'Agent_Test')
    await page.fill('[placeholder="••••"]', '1337')
    await page.click('text=ENTRER')
    await expect(page).toHaveURL(/\/briefing/)
  })

  test('le briefing affiche le lore et le countdown', async ({ page }) => {
    await page.goto('/')
    await page.click('text=Mission E2E')
    await page.fill('[placeholder="••••"]', '1337')
    await page.click('text=ENTRER')
    await page.waitForURL('**/briefing')
    await expect(page.getByText('Test automatisé Playwright')).toBeVisible()
    await expect(page.getByText(/\d{2}:\d{2}/)).toBeVisible() // countdown format MM:SS
  })

  test('le bouton ABORT reset la session et retourne à l\'accueil', async ({ page }) => {
    await page.goto('/')
    await page.click('text=Mission E2E')
    await page.fill('[placeholder="••••"]', '1337')
    await page.click('text=ENTRER')
    await page.waitForURL('**/briefing')
    await page.click('text=ABORT')
    await expect(page).toHaveURL('/')
    // Plus de token — les routes protégées redirigent
    await page.goto('/hunt')
    await expect(page).toHaveURL('/')
  })
})
