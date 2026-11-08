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

async function upload(page: Page, title: string) {
  await page.goto(BASE + '/upload');
  await page.getByLabel('Title').fill(title);
  await page.getByLabel('Module code').fill('CSC312');
  await page.getByLabel('Description').fill('review and delete test');
  await page.getByLabel('File').setInputFiles({ name: 'n.pdf', mimeType: 'application/pdf', buffer: Buffer.from('pdf') });
  await page.getByRole('button', { name: 'Share resource' }).click();
}

async function cardFor(page: Page, title: string) {
  await page.goto(BASE + '/browse?q=' + encodeURIComponent(title));
  return page.locator('.card', { hasText: title }).first();
}

async function logout(page: Page) {
  await page.getByRole('button', { name: 'Log out' }).click();
}

test.describe('Reviews', () => {
  test('owner does not get a review button on their own note', async ({ page }) => {
    await register(page, 'own');
    const title = `OwnNote ${Date.now()}`;
    await upload(page, title);
    const card = await cardFor(page, title);
    await expect(card).toBeVisible();
    await expect(card.getByText('Write a review', { exact: true })).toHaveCount(0);
  });

  test('TC-07: another user can leave a 5-star review', async ({ page }) => {
    await register(page, 'owner');
    const title = `ReviewMe ${Date.now()}`;
    await upload(page, title);
    await logout(page);

    const reviewer = await register(page, 'reviewer');
    let card = await cardFor(page, title);
    await expect(card).toContainText('No ratings yet');
    await card.getByText('Write a review', { exact: true }).click();
    await card.getByPlaceholder('Say something helpful (optional)').fill('Very helpful notes');
    await card.getByRole('button', { name: 'Submit review' }).click();

    card = await cardFor(page, title);
    await expect(card).toContainText('5.0');
    await expect(card).toContainText('1 review');
    await expect(card).toContainText('Very helpful notes');
    await expect(card).toContainText(reviewer);
  });

  test('a reviewer can delete their own review', async ({ page }) => {
    await register(page, 'owner2');
    const title = `ReviewDel ${Date.now()}`;
    await upload(page, title);
    await logout(page);

    await register(page, 'reviewer2');
    let card = await cardFor(page, title);
    await card.getByText('Write a review', { exact: true }).click();
    await card.getByPlaceholder('Say something helpful (optional)').fill('to be removed');
    await card.getByRole('button', { name: 'Submit review' }).click();

    card = await cardFor(page, title);
    await expect(card).toContainText('to be removed');
    await card.getByText('Delete', { exact: true }).click();

    card = await cardFor(page, title);
    await expect(card).not.toContainText('to be removed');
  });
});

test.describe('Delete note', () => {
  test('TC-08: owner can delete their note from the profile', async ({ page }) => {
    await register(page, 'del');
    const title = `DeleteMe ${Date.now()}`;
    await upload(page, title);

    await page.goto(BASE + '/profile');
    const row = page.locator('li', { hasText: title });
    await expect(row).toBeVisible();

    page.on('dialog', d => d.accept());
    await row.getByRole('button', { name: 'Delete' }).click();

    await expect(page.getByText('Note deleted.')).toBeVisible();
    await expect(page.getByText(title)).toHaveCount(0);

    await page.goto(BASE + '/browse');
    await expect(page.getByText(title)).toHaveCount(0);
  });
});