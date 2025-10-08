import { test, expect } from '@playwright/test'

test('loads dashboard', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'Auth' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Ideas' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Admin Tools' })).toBeVisible()

  await expect(page.getByTestId('idea-title-input')).toBeVisible()
  await expect(page.getByTestId('idea-description-input')).toBeVisible()
})
