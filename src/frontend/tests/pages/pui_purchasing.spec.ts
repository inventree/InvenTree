import { Page } from '@playwright/test';

import { expect, test } from '../baseFixtures';
import { adminuser, baseUrl, user } from '../defaults';
import { doLogin } from '../login';
import { TestSetting, setGlobalSetting, setGlobalSettings } from '../settings';

// These tests modify settings, and have to run sequentially
// Each test will reset settings with its afterEach hook
test.describe.configure({ mode: 'serial' });

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
  await setGlobalSetting(page, {
    slug: 'purchaseorders',
    key: 'PURCHASE_ORDER_APPROVE_ALL_GROUP',
    state: 'all access'
  });
}

async function setPurchaser(page: Page) {
  await doLogin(page, adminuser.username, adminuser.password);
  await setGlobalSetting(page, {
    slug: 'purchaseorders',
    key: 'PURCHASE_ORDER_PURCHASER_GROUP',
    state: 'all access'
  });
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
      state: null
    },
    {
      slug: 'purchaseorders',
      key: 'PURCHASE_ORDER_PURCHASER_GROUP',
      state: null
    }
  ];

  await setGlobalSettings(page, settings);
}

/**
 * Creating a new Purchase Order for each test
 * Orders cannot roll back state after being issued.
 * To prevent problems, every test uses its own PO.
 */
test.beforeEach(async ({ page }) => {
  await doLogin(page, adminuser.username, adminuser.password);
  await page.goto(`${baseUrl}/purchasing/index/purchaseorders`);
  await page.locator('table').waitFor();
  await page
    .locator('button[aria-label="action-button-add-purchase-order"]')
    .click();
  await page.locator('section[aria-modal="true"]').waitFor();
  await page
    .getByRole('dialog')
    .locator('div[name="supplier"]')
    .locator('input')
    .click();
  await page
    .locator('div[role="listbox"]')
    .getByText('Arrow', { exact: true })
    .click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();
});

/**
 * Log in as admin and disable all settings that were changed.
 */
test.afterEach(async ({ page }) => {
  await doLogin(page, adminuser.username, adminuser.password);
  await disableAllSettings(page);
});

test('PUI - Pages - Purchasing - Pending transitions', async ({ page }) => {
  // Get URL of PO generated before test
  const url = page.url();

  // All state altering settings disabled
  await expect(page.getByRole('button', { name: 'Issue Order' })).toBeEnabled();
  await page.getByRole('button', { name: 'Issue Order' }).click();
  await expect(page.getByRole('button', { name: 'Submit' })).toBeEnabled();

  // Enable Ready Setting
  await toggleReady(page);

  // Check that Ready Button is present
  await page.goto(url);
  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();
  await page.getByRole('button', { name: 'Ready' }).isEnabled();
  await page.getByRole('button', { name: 'Ready' }).click();
  await page.getByRole('button', { name: 'Submit' }).isEnabled();

  // Enable Approvals (Approvals come before Ready, so Ready is not disabled)
  await toggleApprovals(page);

  await page.goto(url);
  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();
  await page.getByRole('button', { name: 'Request Approval' }).isEnabled();
  await page.getByRole('button', { name: 'Request Approval' }).click();
  await page.getByRole('button', { name: 'Submit' }).isEnabled();
});

test('PUI - Pages - Purchasing - In Approval transitions', async ({ page }) => {
  const url = page.url();
  await toggleApprovals(page);
  await setApprover(page);

  await page.goto(url);
  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();
  await page.getByRole('button', { name: 'Request Approval' }).click();

  const modal = page.getByRole('dialog');
  await modal.getByRole('button', { name: 'Submit' }).click();
  await modal.waitFor({ state: 'hidden' });

  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();
  await page.getByRole('button', { name: 'Approve' }).waitFor();
  await page.getByRole('button', { name: 'Approve' }).isDisabled();
  await page.getByRole('button', { name: 'Recall' }).isEnabled();
  await page.getByRole('button', { name: 'Recall' }).click();

  await modal.waitFor();
  await modal.getByText('Recall Purchase Order').isVisible();
  await modal.getByRole('button', { name: 'Submit' }).isEnabled();

  await doLogin(page, user.username, user.password);

  await page.goto(url);
  await page.getByRole('button', { name: 'Approve' }).isEnabled();
  await page.getByRole('button', { name: 'Approve' }).click();
  await modal.waitFor();
  await modal.getByText('Approve Purchase Order').isVisible();
  await modal.getByRole('button', { name: 'Submit' }).isEnabled();
  await modal.getByRole('button', { name: 'Cancel' }).click();
  await page.getByRole('button', { name: 'Reject' }).isEnabled();
  await page.getByRole('button', { name: 'Reject' }).click();
  await modal.waitFor();
  await modal.getByLabel('Reject Reason').isVisible();
});

test('PUI - Pages - Purchasing - Ready Transitions', async ({ page }) => {
  // Get URL of PO generated before test
  const url = page.url();

  // Standard modal locator
  const modal = page.getByRole('dialog');

  await toggleReady(page);

  await page.goto(url);
  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();
  await expect(page.getByRole('button', { name: 'Ready' })).toBeEnabled();
  await page.getByRole('button', { name: 'Ready' }).click();

  await modal.getByRole('button', { name: 'Submit' }).click();
  await modal.waitFor({ state: 'hidden' });

  await expect(page.getByRole('button', { name: 'Issue Order' })).toBeEnabled();
  await expect(page.getByRole('button', { name: 'Recall' })).toBeEnabled();
  await page.getByRole('button', { name: 'Recall' }).click();

  await modal.waitFor();
  await expect(modal.getByText('Recall Purchase Order')).toBeVisible();
  await expect(modal.getByRole('button', { name: 'Submit' })).toBeEnabled();
  await modal.getByRole('button', { name: 'Cancel' }).click();
  await modal.waitFor({ state: 'hidden' });

  await page.getByRole('button', { name: 'Issue Order' }).click();

  await modal.waitFor();
  await expect(modal.getByText('Issue Order')).toBeVisible();
  await expect(modal.getByRole('button', { name: 'Submit' })).toBeEnabled();

  await setPurchaser(page);

  await page.goto(url);
  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();
  await expect(
    page.getByRole('button', { name: 'Issue Order' })
  ).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Recall' })).toBeEnabled();
});

test('PUI - Pages - Purchasing - Placed Transitions', async ({ page }) => {
  const url = page.url();

  const modal = page.getByRole('dialog');

  await page.getByRole('button', { name: 'Issue Order' }).click();
  modal.waitFor();
  await modal.getByRole('button', { name: 'Submit' }).click();
  modal.waitFor({ state: 'hidden' });

  await page.getByRole('button', { name: 'Complete' }).waitFor();
  await page.getByRole('button', { name: 'Complete' }).click();
  await expect(modal.getByText('Complete Purchase Order')).toBeVisible();
  await expect(
    modal.getByText('All line items have been received')
  ).toBeVisible();
  await modal.getByRole('button', { name: 'Cancel' }).click();
});
