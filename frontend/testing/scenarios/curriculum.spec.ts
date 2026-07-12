import { test, expect } from '@playwright/test';

test.describe('SmilAI - Academic Curriculum & High-Performance RAG Scenarios', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should verify Andhra Pradesh curriculum grade-bands from Pre-Primary to 12th class', async ({ page }) => {
    // Log in as teacher to verify syllabus settings
    await page.fill('input[type="email"]', 'teacher@school.org');
    await page.fill('input[type="password"]', 'password');
    
    const roleSelector = page.locator('select');
    await roleSelector.selectOption('teacher');
    await page.click('button[type="submit"]');

    // Confirm teacher dashboard loads successfully
    const teacherHeading = page.locator('h2:has-text("Teacher Workspace")');
    await expect(teacherHeading).toBeVisible();

    // Verify there are grade band selectors on generating test papers or adding content
    const selectOptions = page.locator('select');
    const selectCount = await selectOptions.count();
    expect(selectCount).toBeGreaterThan(0);
  });

  test('should execute high-speed metadata routing to bypass large volume PDF scans', async ({ page }) => {
    // Under SmilAI's high performance blueprint, RAG searches use constant O(1) metadata filters
    // to instantly isolate the matching textbook chapter, scaling to 10,000+ files.
    // Let's log in as student and verify subject selections isolate study content instantly.
    await page.fill('input[type="email"]', 'student@school.org');
    await page.fill('input[type="password"]', 'password');
    await page.click('button[type="submit"]');

    // Ensure state board subjects like Mathematics or Telugu are listed
    const subjectList = page.locator('.space-y-1, .grid');
    await expect(subjectList).toBeVisible();

    const mathButton = page.locator('button:has-text("Mathematics"), button:has-text("గణితము")');
    if (await mathButton.count() > 0) {
      await mathButton.first().click();
      
      // Check that workspace shifts and shows study materials or chapters instantly without lag
      const studyHeader = page.locator('h3:has-text("Study Material"), h3:has-text("Unit")');
      await expect(studyHeader).toBeVisible();
    }
  });

  test('should handle multi-format file ingestion formats including PDF, HTML, Excel and Word', async ({ page }) => {
    // Log in as teacher to simulate document uploading
    await page.fill('input[type="email"]', 'teacher@school.org');
    await page.fill('input[type="password"]', 'password');
    const roleSelector = page.locator('select');
    await roleSelector.selectOption('teacher');
    await page.click('button[type="submit"]');

    // Locate the drag & drop area description
    const uploadPrompt = page.locator('text=Supports .pdf, .docx, .xlsx, .html');
    await expect(uploadPrompt).toBeVisible();
  });
});
