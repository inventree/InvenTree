import { Page } from '@playwright/test';

import { test } from '../baseFixtures';
import { adminuser, baseUrl } from '../defaults';
import { doLogin, doQuickLogin } from '../login';

async function enableReady(page: Page) {
  await doLogin(page, adminuser.username, adminuser.password);
  await page.goto(`${baseUrl}/settings/system/purchaseorders`);
  await page.getByText('Enable Ready Status').waitFor();
  const setting = page.locator('div', { hasText: 'Enable Ready Status' });
  await setting.getByRole('switch').click();
}

async function enableApprovals(page: Page) {
  await doLogin(page, adminuser.username, adminuser.password);
  await page.goto(`${baseUrl}/settings/system/purchaseorders`);
  await page.getByText('Purchase Order Approvals').waitFor();
  const setting = page.locator('div', { hasText: 'Purchase Order Approvals' });
  await setting.getByRole('switch').click();
}

async function setApprover(page: Page) {
  await doLogin(page, adminuser.username, adminuser.password);
  await page.goto(`${baseUrl}/settings/system/purchaseorders`);
  await page.getByText('Master approval group').waitFor();
  const setting = page.locator('div', { hasText: 'Master approval group' });
  await setting.getByRole('button').click();
  await page.getByLabel('Master approval group').fill('all access');
  await page.getByRole('button', { name: 'Submit' }).click();
}

test('PUI - Pages - Purchasing - Pending transitions', async ({ page }) => {
  await doQuickLogin(page);

  // All state altering settings disabled
  await page.goto(`${baseUrl}/purchasing/purchase-order/12/detail`);
  await page.getByText('Purchase Order: PO0012').waitFor();
  await page.getByRole('button', { name: 'Issue Order' }).isEnabled();

  await enableReady(page);

  // Check that Ready Button is present
  await page.goto(`${baseUrl}/purchasing/purchase-order/12/detail`);
  await page.getByText('Purchase Order: PO0012').waitFor();
  await page.getByRole('button', { name: 'Ready' }).isEnabled();

  await enableApprovals(page);

  await page.goto(`${baseUrl}/purchasing/purchase-order/12/detail`);
  await page.getByText('Purchase Order: PO0012').waitFor();
  await page.getByRole('button', { name: 'Request Approval' }).isEnabled();
});

test('PUI - Pages - Purchasing - In Approval transitions', async ({ page }) => {
  await enableApprovals(page);

  await page.goto(`${baseUrl}/purchasing/purchase-order/12/detail`);
  await page.getByText('Purchase Order: PO0012').waitFor();
  await page.getByRole('button', { name: 'Request Approval' }).click();

  await page.getByText('Request approval of order').waitFor();
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('Purchase Order: PO0012').waitFor();
  await page.getByRole('button', { name: 'Approve' }).isDisabled();
  await page.getByRole('button', { name: 'Recall' }).isEnabled();

  await setApprover(page);

  await page.goto(`${baseUrl}/purchasing/purchase-order/12/detail`);
  await page.getByRole('button', { name: 'Approve' }).isEnabled();
  await page.getByRole('button', { name: 'Reject' }).isEnabled();
});
