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

async function upload(page: Page, title: string, module: string, desc: string) {
  await page.goto(BASE + '/upload');
  await page.getByLabel('Title').fill(title);
  await page.getByLabel('Module code').fill(module);
  await page.getByLabel('Description').fill(desc);
  await page.getByLabel('File').setInputFiles({ name: 'n.pdf', mimeType: 'application/pdf', buffer: Buffer.from('pdf') });
  await page.getByRole('button', { name: 'Share resource' }).click();
}

test.describe('Navigation', () => {
  test('menu links reach Browse and Upload pages', async ({ page }) => {
    await page.goto(BASE + '/');
    await page.getByRole('link', { name: 'Browse', exact: true }).first().click();
    await expect(page).toHaveURL(/browse/);
    await register(page, 'nav');
    await page.getByRole('link', { name: 'Upload', exact: true }).first().click();
    await expect(page).toHaveURL(/upload/);
  });
});

test.describe('Register errors', () => {
  test('duplicate username is not accepted twice', async ({ page }) => {
    const u = await register(page, 'dup');
    await page.getByRole('button', { name: 'Log out' }).click();
    await page.goto(BASE + '/register');
    await page.getByRole('textbox', { name: 'Username' }).fill(u);
    await page.getByRole('textbox', { name: 'Email' }).fill(`other${Date.now()}@gmail.com`);
    await page.getByRole('textbox', { name: 'Password' }).fill('testuser1');
    await page.getByRole('button', { name: 'Create account' }).click();
    await expect(page.getByRole('button', { name: 'Log out' })).toHaveCount(0);
  });

  test('empty form is not submitted', async ({ page }) => {
    await page.goto(BASE + '/register');
    await page.getByRole('button', { name: 'Create account' }).click();
    await expect(page).toHaveURL(/register/);
  });
});

test.describe('Access control', () => {
  test('logged-out user cannot use the upload page', async ({ page }) => {
    await page.goto(BASE + '/upload');
    await expect(page.getByRole('button', { name: 'Share resource' })).toHaveCount(0);
  });
});

test.describe('Upload validation', () => {
  test('invalid module code is rejected', async ({ page }) => {
    await register(page, 'val');
    const title = `BadModule ${Date.now()}`;
    await upload(page, title, '123', 'should not be saved');
    await page.goto(BASE + '/browse');
    await page.getByLabel('Search study resources').fill(title);
    await page.getByRole('button', { name: 'Find notes' }).click();
    await expect(page.getByText('No resources found')).toBeVisible();
  });
});

test.describe('Search', () => {
  test('search finds a resource by module code', async ({ page }) => {
    await register(page, 'mod');
    const title = `ByModule ${Date.now()}`;
    await upload(page, title, 'MAT111', 'module code search');
    await page.goto(BASE + '/browse');
    await page.getByLabel('Search study resources').fill('MAT111');
    await page.getByRole('button', { name: 'Find notes' }).click();
    await expect(page.getByText(title)).toBeVisible();
  });

  test('search finds a resource by description', async ({ page }) => {
    await register(page, 'desc');
    const word = `uniqueword${Date.now()}`;
    const title = `ByDesc ${Date.now()}`;
    await upload(page, title, 'CSC312', `contains ${word}`);
    await page.goto(BASE + '/browse');
    await page.getByLabel('Search study resources').fill(word);
    await page.getByRole('button', { name: 'Find notes' }).click();
    await expect(page.getByText(title)).toBeVisible();
  });

  test('search is not case sensitive', async ({ page }) => {
    await register(page, 'case');
    const title = `CaseTest ${Date.now()}`;
    await upload(page, title, 'CSC312', 'case test');
    await page.goto(BASE + '/browse');
    await page.getByLabel('Search study resources').fill(title.toUpperCase());
    await page.getByRole('button', { name: 'Find notes' }).click();
    await expect(page.getByText(title)).toBeVisible();
  });
});