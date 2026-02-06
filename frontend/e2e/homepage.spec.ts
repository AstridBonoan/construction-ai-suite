import { test, expect } from '@playwright/test';

test('homepage shows Phase 10 title', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/Phase 10 - Operator UI/i);
  // ensure main root exists
  await expect(page.locator('#root')).toBeVisible();
});
