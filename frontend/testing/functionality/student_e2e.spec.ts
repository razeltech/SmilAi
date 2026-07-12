import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Student E2E Walkthrough', () => {
  // Ensure the screenshots directory exists
  test.beforeAll(() => {
    const dir = path.join(process.cwd(), 'screenshots');
    if (!fs.existsSync(dir)){
        fs.mkdirSync(dir, { recursive: true });
    }
  });

  test('Student login and chat interaction', async ({ page }) => {
    // Mock API responses to avoid needing the real backend running
    await page.route('**/v1/org-settings', route => route.fulfill({ json: { name: 'SmilAI School', theme: 'light' } }));
    
    await page.route('**/v1/auth/login', route => route.fulfill({
      json: { id: 'student_123', name: 'Rahul Kumar', email: 'rahul@school.org', role: 'student', org_id: 'org_1' }
    }));
    
    await page.route('**/v1/subjects*', route => route.fulfill({
      json: [{ id: 'math_101', name: 'Mathematics', teacherId: 'teacher_1' }]
    }));
    
    await page.route('**/v1/chat/sessions*', route => route.fulfill({
      json: [{ id: 'sess_1', title: 'Math Basics' }]
    }));
    
    await page.route('**/v1/chat/sessions/sess_1/messages', route => route.fulfill({
      json: []
    }));
    
    await page.route('**/v1/subjects/math_101/assignments', route => route.fulfill({ json: [] }));
    await page.route('**/v1/subjects/math_101/assessments', route => route.fulfill({ json: [] }));
    await page.route('**/v1/subjects/math_101/documents', route => route.fulfill({ json: [] }));
    await page.route('**/v1/students/*/subjects/*/record', route => route.fulfill({ json: { grade: 'A' } }));
    await page.route('**/v1/users/*/profile', route => route.fulfill({ json: { name: 'Rahul' } }));

    // Mock the streaming chat response
    await page.route('**/v1/chat/stream', async route => {
      route.fulfill({
        status: 200,
        contentType: 'text/plain',
        body: 'A computer is a machine that processes information based on instructions.'
      });
    });

    // 1. Navigate to the application
    await page.goto('http://localhost:5173');
    
    // Wait for the Auth screen to render
    await page.waitForSelector('#quick-login-student', { timeout: 10000 });
    await page.screenshot({ path: 'screenshots/01_auth_screen.png' });

    // 2. Login as a student using explicit inputs
    await page.fill('#auth-email-input', 'rahul@school.org');
    await page.fill('#auth-password-input', 'password');
    await page.click('#auth-submit-btn');
    
    // Check if error happens, screenshot it
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'screenshots/01_after_login_attempt.png' });

    // 3. Wait for the Dashboard to load and stabilize
    await page.waitForSelector('#student-chat-input', { timeout: 15000 });
    // Let the animations settle
    await page.waitForTimeout(2000); 
    await page.screenshot({ path: 'screenshots/02_student_dashboard.png' });

    // 4. Send a message to SmilAI
    await page.fill('#student-chat-input', 'Hello SmilAI! How does a computer work?');
    await page.screenshot({ path: 'screenshots/03_chat_input_filled.png' });
    await page.click('#student-chat-send-btn');

    // 5. Wait for the Assistant to respond
    // A placeholder message id starts with ast-
    // But we can just wait for text in the assistant's bubble, or wait a few seconds
    await page.waitForTimeout(5000); // Wait 5 seconds for streaming to happen
    await page.screenshot({ path: 'screenshots/04_chat_response.png' });

    // 6. Switch to Code Workspace
    await page.click('#workspace-code-btn', { force: true });
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'screenshots/05_code_workspace.png' });
    
    // 7. Switch to Test Workspace
    await page.click('#workspace-test-btn', { force: true });
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'screenshots/06_test_workspace.png' });

    // 8. Switch to Profile Workspace
    await page.click('#workspace-profile-btn', { force: true });
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'screenshots/07_profile_workspace.png' });

  });
});
