import { Page } from '@playwright/test';

import { expect, test } from '../baseFixtures';
import { adminuser, baseUrl } from '../defaults';
import { doLogin, doQuickLogin } from '../login';
import { TestSetting, setGlobalSetting, setGlobalSettings } from '../settings';

async function toggleReady(page: Page, disable = false) {
  await doLogin(page, adminuser.username, adminuser.password);
  await setGlobalSetting(page, {
    slug: 'purchaseorders',
    key: 'ENABLE_PURCHASE_ORDER_READY_STATUS',
    state: !disable,
    isToggle: true
  });
}

async function toggleApprovals(page: Page, disable = false) {
  await doLogin(page, adminuser.username, adminuser.password);
  await setGlobalSetting(page, {
    slug: 'purchaseorders',
    key: 'ENABLE_PURCHASE_ORDER_APPROVAL',
    state: !disable,
    isToggle: true
  });
}

async function setApprover(page: Page) {
  await doLogin(page, adminuser.username, adminuser.password);
  await page.goto(`${baseUrl}/settings/system/purchaseorders`);
  await page.getByText('Master approval group').waitFor();
  await expect(
    page.getByTestId('PURCHASE_ORDER_PURCHASER_GROUP')
  ).toBeVisible();
  await expect(
    page.getByTestId('PURCHASE_ORDER_PURCHASER_GROUP').getByRole('button')
  ).toBeVisible();
  //  await page.getByText('Edit Setting').waitFor();
  //  await page.getByLabel('Master approval group').fill('all access');
  //  await page.getByRole('button', { name: 'Submit' }).click();
}

async function disableAllSettings(page: Page) {
  const settings: TestSetting[] = [
    {
      slug: 'purchaseorders',
      key: 'ENABLE_PURCHASE_ORDER_APPROVAL',
      state: false,
      isToggle: true
    },
    {
      slug: 'purchaseorders',
      key: 'ENABLE_PURCHASE_ORDER_READY_STATUS',
      state: false,
      isToggle: true
    },
    {
      slug: 'purchaseorders',
      key: 'PURCHASE_ORDER_APPROVE_ALL_GROUP',
      state: ''
    },
    {
      slug: 'purchaseorders',
      key: 'PURCHASE_ORDER_PURCHASER_GROUP',
      state: ''
    }
  ];

  await setGlobalSettings(page, settings);
}

test.afterEach(async ({ page }) => {
  await disableAllSettings(page);
});

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
