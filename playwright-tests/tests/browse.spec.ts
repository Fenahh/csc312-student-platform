import { test, expect } from '@playwright/test';

test('browse page shows the search controls', async ({ page }) => {
  await page.goto('http://127.0.0.1:5000/browse');

  await expect(page.getByRole('heading', { name: 'Find your next study resource.' })).toBeVisible();
  await expect(page.getByLabel('Search study resources')).toBeVisible();
  await expect(page.getByLabel('Module', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Find notes' })).toBeVisible();
});

test('searching with no matches shows the empty message', async ({ page }) => {
  await page.goto('http://127.0.0.1:5000/browse');

  await page.getByLabel('Search study resources').fill('zzz-no-such-resource');
  await page.getByRole('button', { name: 'Find notes' }).click();

  await expect(page.getByText('No resources found')).toBeVisible();
  await expect(page.getByText('0 resources found')).toBeVisible();
});