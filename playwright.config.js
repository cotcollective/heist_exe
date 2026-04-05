import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  retries: 1,
  reporter: [['list'], ['html', { outputFolder: 'e2e/report', open: 'never' }]],
  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost',
    // Simule un iPhone — c'est une PWA mobile
    ...devices['iPhone 13'],
    locale: 'fr-CA',
    geolocation: { latitude: 45.5680, longitude: -73.5490 },
    permissions: ['geolocation'],
    // Screenshots sur échec
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 13'] },
    },
  ],
})
