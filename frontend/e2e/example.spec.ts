import { test, expect } from '@playwright/test'

test('loads dashboard', async ({ page }) => {
  await page.goto('http://localhost:5173')
  await expect(page.getByText('AI Hub Dashboard')).toBeVisible()
})

