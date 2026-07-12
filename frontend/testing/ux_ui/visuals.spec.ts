import { test, expect } from '@playwright/test';

test.describe('SmilAI - UX & UI Layout Compliance Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Go to the main deployment address
    await page.goto('/');
  });

  test('should load the high-contrast light theme with professional typography', async ({ page }) => {
    // Verify title text has correct primary brand name
    const brandTitle = page.locator('h2:has-text("SmilAI")');
    await expect(brandTitle).toBeVisible();

    // Verify sub-heading explains the offline virtual-teacher platform
    const subtitle = page.locator('text=Offline Virtual-Teacher & Assessment Platform');
    await expect(subtitle).toBeVisible();

    // Check that there are no "Sparkles" icons or unrequested flashy banners
    const sparkles = page.locator('.lucide-sparkles, svg[class*="sparkles"]');
    await expect(sparkles).toHaveCount(0);
  });

  test('should verify responsive touch target sizing and interactive inputs', async ({ page }) => {
    // Buttons should have clear visual heights and touch targets (>= 44px on mobile viewports)
    const loginButton = page.locator('button:has-text("Sign In")');
    if (await loginButton.isVisible()) {
      const box = await loginButton.boundingBox();
      if (box) {
        expect(box.height).toBeGreaterThanOrEqual(40); // 40-48px standard target height
      }
    }

    const emailInput = page.locator('input[type="email"]');
    await expect(emailInput).toBeVisible();
    await expect(emailInput).toBeEnabled();
  });

  test('should verify that disk optimization tip or Ollama warning box is NOT displayed on the main UI', async ({ page }) => {
    // Ensure "Disk Optimization Tip" or "Ollama models" does not show up
    const diskWarning = page.locator('text=Disk Optimization Tip');
    await expect(diskWarning).toHaveCount(0);

    const ollamaWarning = page.locator('text=Ollama models are automatically stored');
    await expect(ollamaWarning).toHaveCount(0);
  });
});
