import { test, expect, Page } from '@playwright/test';

const BASE = 'http://127.0.0.1:5000';

async function register(page: Page, name: string) {
  const u = `${name}${Date.now()}${Math.floor(Math.random() * 1000)}`;
  await page.goto(BASE + '/');
  await page.getByRole('link', { name: 'Create an account' }).click();
  await page.getByRole('textbox', { name: 'Username' }).fill(u);
  await page.getByRole('textbox', { name: 'Email' }).fill(`${u}@gmail.com`);
  await page.getByRole('textbox', { name: 'Password' }).fill('testuser1');
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible();
  return u;
}

test.describe('Login errors and access control', () => {
  test('wrong password shows an error and does not log in', async ({ page }) => {
    const u = await register(page, 'wp');
    await page.getByRole('button', { name: 'Log out' }).click();
    await page.goto(BASE + '/login');
    await page.getByLabel('Username or email').fill(u);
    await page.getByLabel('Password').fill('wrong-password');
    await page.getByRole('button', { name: 'Login', exact: true }).click();
    await expect(page.getByText('Username or password is incorrect.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Log out' })).toHaveCount(0);
  });

  test('unknown user shows the same error', async ({ page }) => {
    await page.goto(BASE + '/login');
    await page.getByLabel('Username or email').fill(`nobody${Date.now()}`);
    await page.getByLabel('Password').fill('whatever123');
    await page.getByRole('button', { name: 'Login', exact: true }).click();
    await expect(page.getByText('Username or password is incorrect.')).toBeVisible();
  });

  test('user can log back in after logging out', async ({ page }) => {
    const u = await register(page, 'relog');
    await page.getByRole('button', { name: 'Log out' }).click();
    await page.goto(BASE + '/login');
    await page.getByLabel('Username or email').fill(u);
    await page.getByLabel('Password').fill('testuser1');
    await page.getByRole('button', { name: 'Login', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible();
  });

  test('user can log in with their email address', async ({ page }) => {
    const u = await register(page, 'mail');
    await page.getByRole('button', { name: 'Log out' }).click();
    await page.goto(BASE + '/login');
    await page.getByLabel('Username or email').fill(`${u}@gmail.com`);
    await page.getByLabel('Password').fill('testuser1');
    await page.getByRole('button', { name: 'Login', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible();
  });

  test('logged-out visitor is redirected from Upload to Login', async ({ page }) => {
    await page.goto(BASE + '/upload');
    await expect(page).toHaveURL(/login\?next=%2Fupload/);
    await expect(page.getByRole('heading', { name: 'Login' })).toBeVisible();
  });

  test('logged-out visitor is redirected from Profile to Login', async ({ page }) => {
    await page.goto(BASE + '/profile');
    await expect(page).toHaveURL(/login/);
  });
});