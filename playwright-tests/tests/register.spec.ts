import { test, expect } from '@playwright/test';

test('register page shows the sign-up form', async ({ page }) => {
  await page.goto('http://127.0.0.1:5000/');
  await page.getByRole('link', { name: 'Create an account' }).click();

  await expect(page.getByRole('textbox', { name: 'Username' })).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Email' })).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Password' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Create account' })).toBeVisible();
});

test('a new user can register', async ({ page }) => {
  const unique = Date.now();

  await page.goto('http://127.0.0.1:5000/');
  await page.getByRole('link', { name: 'Create an account' }).click();

  await page.getByRole('textbox', { name: 'Username' }).fill(`sia${unique}`);
  await page.getByRole('textbox', { name: 'Email' }).fill(`sia${unique}@gmail.com`);
  await page.getByRole('textbox', { name: 'Password' }).fill('testuser1');
  await page.getByRole('button', { name: 'Create account' }).click();

  // Placeholder check: we leave the register page after success
  await expect(page).not.toHaveURL(/register/);
});