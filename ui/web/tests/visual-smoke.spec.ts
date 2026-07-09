import { expect, test } from '@playwright/test';

// Optional browser smoke scaffold for POST-H-028-C.
// It is intentionally not required by core pytest. Install @playwright/test and
// run a local Vite preview/dev server explicitly before using this browser test.

test('critical local dashboard renders visual smoke markers', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /DevPilot Local Dashboard/i })).toBeVisible();
  await expect(page.getByText(/Local-first/i).first()).toBeVisible();
  await expect(page.getByText(/No remote/i).first()).toBeVisible();
  await expect(page.getByText(/Operator Dashboard/i).first()).toBeVisible();
  await expect(page.getByText(/Report Viewer/i).first()).toBeVisible();
  await expect(page.getByText(/Trace Viewer/i).first()).toBeVisible();
  await expect(page.getByText(/Approval Center/i).first()).toBeVisible();
  await expect(page.getByText(/Settings UI/i).first()).toBeVisible();
});
