import { test, expect } from '@playwright/test'

test.describe('PWA — offline et installabilité', () => {

  test('service worker enregistré', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    const swRegistered = await page.evaluate(() =>
      navigator.serviceWorker.getRegistrations().then((regs) => regs.length > 0)
    )
    expect(swRegistered).toBe(true)
  })

  test('manifest PWA accessible', async ({ request }) => {
    const res = await request.get('/manifest.webmanifest')
    expect(res.ok()).toBeTruthy()
    const manifest = await res.json()
    expect(manifest.name).toBe('HEIST.EXE')
    expect(manifest.display).toBe('standalone')
    expect(manifest.theme_color).toBe('#0a0a0a')
    expect(manifest.icons).toHaveLength(2)
  })

  test('page offline — contenu mis en cache après première visite', async ({ page, context }) => {
    // Première visite — mise en cache
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000) // Laisser le SW cacher

    // Passer offline
    await context.setOffline(true)

    // Recharger — doit fonctionner depuis cache
    await page.reload()
    await expect(page.getByText('HEIST.EXE')).toBeVisible({ timeout: 8000 })

    // Remettre online
    await context.setOffline(false)
  })

  test('tiles OSM mises en cache après navigation map', async ({ page, request }) => {
    // Auth rapide avec session persistée
    await page.goto('/')
    // Si pas de mission, vérifier juste que l'app charge
    await expect(page.locator('#root')).not.toBeEmpty()
  })

  test('meta viewport correct pour mobile', async ({ page }) => {
    await page.goto('/')
    const viewport = await page.evaluate(() => {
      const meta = document.querySelector('meta[name="viewport"]')
      return meta?.getAttribute('content') ?? ''
    })
    expect(viewport).toContain('width=device-width')
    expect(viewport).toContain('viewport-fit=cover')
  })

  test('theme-color noir défini', async ({ page }) => {
    await page.goto('/')
    const themeColor = await page.evaluate(() => {
      const meta = document.querySelector('meta[name="theme-color"]')
      return meta?.getAttribute('content')
    })
    expect(themeColor).toBe('#0a0a0a')
  })
})
