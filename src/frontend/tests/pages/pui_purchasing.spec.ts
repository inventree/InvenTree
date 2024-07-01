import { Page } from '@playwright/test';

import { test } from '../baseFixtures';
import { adminuser, baseUrl } from '../defaults';
import { doLogin, doQuickLogin } from '../login';

async function toggleReady(page: Page, disable = false) {
  await doLogin(page, adminuser.username, adminuser.password);
  await page.goto(`${baseUrl}/settings/system/purchaseorders`);
  await page.getByText('Enable Ready Status').waitFor();
  const settingText = page.locator('text=Enable Ready Status');
  const settingParent = settingText.locator('..').locator('..');
  const toggle = settingParent.getByRole('button');
  const state = await toggle.isChecked();
  await settingParent.getByRole('button').click();
}

async function toggleApprovals(page: Page) {
  await doLogin(page, adminuser.username, adminuser.password);
  await page.goto(`${baseUrl}/settings/system/purchaseorders`);
  await page.getByText('Purchase Order Approvals').waitFor();
  const settingText = page.locator('text=Purchase Order Approvals');
  const settingParent = settingText.locator('..');
  await settingParent.getByRole('switch').click();
}

async function setApprover(page: Page) {
  await doLogin(page, adminuser.username, adminuser.password);
  await page.goto(`${baseUrl}/settings/system/purchaseorders`);
  await page.getByText('Master approval group').waitFor();
  const settingText = page.locator('text=Master approval group');
  const settingParent = settingText.locator('..');
  await settingParent.getByRole('switch').click();
  await page.getByLabel('Master approval group').fill('all access');
  await page.getByRole('button', { name: 'Submit' }).click();
}

test('PUI - Pages - Purchasing - Pending transitions', async ({ page }) => {
  await doQuickLogin(page);

  // All state altering settings disabled
  await page.goto(`${baseUrl}/purchasing/purchase-order/12/detail`);
  await page.getByText('Purchase Order: PO0012').waitFor();
  await page.getByRole('button', { name: 'Issue Order' }).isEnabled();

  await toggleReady(page);

  // Check that Ready Button is present
  await page.goto(`${baseUrl}/purchasing/purchase-order/12/detail`);
  await page.getByText('Purchase Order: PO0012').waitFor();
  await page.getByRole('button', { name: 'Ready' }).isEnabled();

  await toggleApprovals(page);

  await page.goto(`${baseUrl}/purchasing/purchase-order/12/detail`);
  await page.getByText('Purchase Order: PO0012').waitFor();
  await page.getByRole('button', { name: 'Request Approval' }).isEnabled();
});

test('PUI - Pages - Purchasing - In Approval transitions', async ({ page }) => {
  await toggleApprovals(page);

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
