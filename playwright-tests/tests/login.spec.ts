import { test, expect } from '@playwright/test';

test('a registered user can log in and out', async ({ page }) => {
  const unique = Date.now();
  const username = `sia${unique}`;
  const email = `sia${unique}@gmail.com`;
  const password = 'testuser1';

  // Register a fresh account
  await page.goto('http://127.0.0.1:5000/');
  await page.getByRole('link', { name: 'Create an account' }).click();
  await page.getByRole('textbox', { name: 'Username' }).fill(username);
  await page.getByRole('textbox', { name: 'Email' }).fill(email);
  await page.getByRole('textbox', { name: 'Password' }).fill(password);
  await page.getByRole('button', { name: 'Create account' }).click();

  // After registering we are logged in: Log out button is visible
  await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible();

  // Log out, and check the Login link comes back
  await page.getByRole('button', { name: 'Log out' }).click();
  await expect(page.getByRole('link', { name: 'Login' })).toBeVisible();
});