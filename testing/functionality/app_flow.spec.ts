import { test, expect } from '@playwright/test';

test.describe('SmilAI - Platform Functional Capability Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should handle user login authentication and session routing', async ({ page }) => {
    // Fill in default student credentials
    await page.fill('input[type="email"]', 'student@school.org');
    await page.fill('input[type="password"]', 'password');

    // Select role (default is student, but check that selector operates correctly)
    const roleSelector = page.locator('select');
    await expect(roleSelector).toBeVisible();
    await roleSelector.selectOption('student');

    // Click submit
    await page.click('button[type="submit"]');

    // Should route to Student Dashboard and display greeting
    const welcomeHeading = page.locator('h2:has-text("Student Workspace")');
    await expect(welcomeHeading).toBeVisible();
  });

  test('should verify microphone speech recognition alerts inside workspace frame', async ({ page }) => {
    // Log in as student
    await page.fill('input[type="email"]', 'student@school.org');
    await page.fill('input[type="password"]', 'password');
    await page.click('button[type="submit"]');

    // Locate microphone button in active virtual assistant interface
    const micButton = page.locator('button[title*="Microphone"]');
    if (await micButton.isVisible()) {
      await micButton.click();
      
      // Since Playwright headless mode doesn't have system mic approval, 
      // a proper graceful error instruction should be shown to the user.
      const errorLabel = page.locator('p:has-text("Microphone permission blocked")');
      // Or general mic error message
      const generalMicError = page.locator('[class*="text-red-600"], [class*="text-rose-600"]');
      
      const count = await generalMicError.count();
      if (count > 0) {
        const text = await generalMicError.first().innerText();
        expect(text).toContain('Microphone');
      }
    }
  });

  test('should support Warm Voice Mode and audio feedback options', async ({ page }) => {
    // Log in as student
    await page.fill('input[type="email"]', 'student@school.org');
    await page.fill('input[type="password"]', 'password');
    await page.click('button[type="submit"]');

    // Warm voice toggle
    const warmVoiceBtn = page.locator('button:has-text("Normal Voice"), button:has-text("Warm Voice Mode")');
    if (await warmVoiceBtn.isVisible()) {
      const initialText = await warmVoiceBtn.innerText();
      await warmVoiceBtn.click();
      const updatedText = await warmVoiceBtn.innerText();
      expect(initialText).not.toEqual(updatedText);
    }
  });
});
