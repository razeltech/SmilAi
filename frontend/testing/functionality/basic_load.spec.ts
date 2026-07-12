import { test, expect } from '@playwright/test';

test('App boots up and renders authentication screen by default', async ({ page }) => {
  // Navigate to the root URL (configured in playwright.config.ts as localhost:5173)
  await page.goto('/');

  // Expect the document to contain the primary SmilAI text or Login screen elements
  await expect(page.locator('body')).toContainText(/Login|SmilAI|Email/i);
});
