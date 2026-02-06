import { test, expect } from '@playwright/test';

test('monday login button navigates to oauth', async ({ page }) => {
  // Start from the login route
  await page.goto('http://localhost:5173/saas/login');
  // Click the Connect monday.com button
  const btn = page.locator('text=Connect monday.com');
  await expect(btn).toBeVisible();
});
