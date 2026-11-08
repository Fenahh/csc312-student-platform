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

async function fillUpload(page: Page, title: string, file: { name: string; mimeType: string; buffer: Buffer }) {
  await page.goto(BASE + '/upload');
  await page.getByLabel('Title').fill(title);
  await page.getByLabel('Module code').fill('CSC312');
  await page.getByLabel('Description').fill('automated upload test');
  await page.getByLabel('File').setInputFiles(file);
  await page.getByRole('button', { name: 'Share resource' }).click();
}

test.describe('File upload', () => {
  test('TC-03: a valid PDF is accepted and listed', async ({ page }) => {
    await register(page, 'pdf');
    const title = `PdfNote ${Date.now()}`;
    await fillUpload(page, title, {
      name: 'notes.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.alloc(2 * 1024 * 1024, 'a'), // 2 MB
    });
    await expect(page.getByText('Uploaded.')).toBeVisible();
    await expect(page.getByText(title)).toBeVisible();
  });

  test('TC-04: an .exe file is rejected', async ({ page }) => {
    await register(page, 'exe');
    const title = `ExeNote ${Date.now()}`;
    await fillUpload(page, title, {
      name: 'virus.exe',
      mimeType: 'application/octet-stream',
      buffer: Buffer.from('MZ fake exe'),
    });
    await expect(page.getByText('Only .pdf, .docx and .png files are allowed.')).toBeVisible();
    await page.goto(BASE + '/browse');
    await expect(page.getByText(title)).toHaveCount(0);
  });
});