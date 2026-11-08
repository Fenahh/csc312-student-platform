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

test.describe('Profile', () => {
  test('new user profile shows their details and no uploads', async ({ page }) => {
    const u = await register(page, 'prof');
    await page.getByRole('link', { name: 'Profile', exact: true }).first().click();
    await expect(page).toHaveURL(/profile/);
    await expect(page.getByRole('heading', { name: u })).toBeVisible();
    await expect(page.getByText(`${u}@gmail.com`)).toBeVisible();
    await expect(page.getByText("You haven't uploaded anything yet")).toBeVisible();
  });

  test('an uploaded resource appears on the profile page', async ({ page }) => {
    await register(page, 'prof2');
    const title = `ProfileUpload ${Date.now()}`;
    await upload(page, title, 'CSC312', 'shows on profile');
    await page.goto(BASE + '/profile');
    await expect(page.getByText(title)).toBeVisible();
  });
});

test.describe('Module filters', () => {
  test('quick filter shows only that module', async ({ page }) => {
    await register(page, 'qf');
    const t1 = `QuickA ${Date.now()}`;
    const t2 = `QuickB ${Date.now()}`;
    await upload(page, t1, 'CSC312', 'csc resource');
    await upload(page, t2, 'MAT111', 'mat resource');
    await page.goto(BASE + '/browse');
    await page.getByRole('link', { name: 'MAT111', exact: true }).click();
    await expect(page.getByText(t2)).toBeVisible();
    await expect(page.getByText(t1)).toHaveCount(0);
  });

  test('module dropdown filters the results', async ({ page }) => {
    await register(page, 'dd');
    const t1 = `DropA ${Date.now()}`;
    const t2 = `DropB ${Date.now()}`;
    await upload(page, t1, 'CSC312', 'csc resource');
    await upload(page, t2, 'MAT111', 'mat resource');
    await page.goto(BASE + '/browse');
    await page.getByLabel('Module', { exact: true }).selectOption('MAT111');
    await page.getByRole('button', { name: 'Find notes' }).click();
    await expect(page.getByText(t2)).toBeVisible();
    await expect(page.getByText(t1)).toHaveCount(0);
  });
});