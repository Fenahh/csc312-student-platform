import { test, expect } from '@playwright/test';

test('an uploaded resource can be found by searching', async ({ page }) => {
  const unique = Date.now();
  const title = `Playwright Notes ${unique}`;

  // Register a fresh account (this also logs us in)
  await page.goto('http://127.0.0.1:5000/');
  await page.getByRole('link', { name: 'Create an account' }).click();
  await page.getByRole('textbox', { name: 'Username' }).fill(`sia${unique}`);
  await page.getByRole('textbox', { name: 'Email' }).fill(`sia${unique}@gmail.com`);
  await page.getByRole('textbox', { name: 'Password' }).fill('testuser1');
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible();

  // Upload a resource
  await page.goto('http://127.0.0.1:5000/upload');
  await page.getByLabel('Title').fill(title);
  await page.getByLabel('Module code').fill('CSC312');
  await page.getByLabel('Description').fill('Notes written by an automated test');
  await page.getByLabel('File').setInputFiles({ name: 'n.pdf', mimeType: 'application/pdf', buffer: Buffer.from('pdf') });
  await page.getByRole('button', { name: 'Share resource' }).click();

  // Search for it on the Browse page
  await page.goto('http://127.0.0.1:5000/browse');
  await page.getByLabel('Search study resources').fill(title);
  await page.getByRole('button', { name: 'Find notes' }).click();

  await expect(page.getByText(title)).toBeVisible();
});