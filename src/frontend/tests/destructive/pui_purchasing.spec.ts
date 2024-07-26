import { Page } from '@playwright/test';

import { expect, test } from '../baseFixtures';
import { baseUrl } from '../defaults';
import { doLogin, doQuickLogin } from '../login';

// CSRF token
let TOKEN: string;
let ORDER_ID: number;

// These tests modify settings, and have to run sequentially
// Each test will reset settings with its afterEach hook
test.describe.configure({ mode: 'serial' });

async function setSettingAPI(
  page: Page,
  key: string,
  value: string | boolean | null
) {
  const settingResponse = await page.request.patch(
    `http://localhost:8000/api/settings/global/${key}/`,
    {
      data: {
        value: value
      },
      headers: {
        'x-csrftoken': TOKEN
      }
    }
  );
  expect(settingResponse.ok()).toBeTruthy();
  return;
}

async function updateToken(page: Page) {
  const cookies = await page.context().cookies();

  for (const cook of cookies) {
    if (cook.name === 'csrftoken') {
      TOKEN = cook.value;
      break;
    }
  }
}

async function toggleReady(page: Page, disable = false) {
  await setSettingAPI(page, 'ENABLE_PURCHASE_ORDER_READY_STATUS', !disable);
}

async function toggleApprovals(page: Page, disable = false) {
  await setSettingAPI(page, 'ENABLE_PURCHASE_ORDER_APPROVAL', !disable);
}

async function setApprover(page: Page, group = 'all access') {
  await setSettingAPI(page, 'PURCHASE_ORDER_APPROVE_ALL_GROUP', group);
}

async function setPurchaser(page: Page, group = 'all access') {
  await setSettingAPI(page, 'PURCHASE_ORDER_PURCHASER_GROUP', group);
}

async function disableAllSettings(page: Page) {
  const settings: { key: string; state: boolean | string }[] = [
    {
      key: 'ENABLE_PURCHASE_ORDER_APPROVAL',
      state: false
    },
    {
      key: 'ENABLE_PURCHASE_ORDER_READY_STATUS',
      state: false
    },
    {
      key: 'PURCHASE_ORDER_APPROVE_ALL_GROUP',
      state: ''
    },
    {
      key: 'PURCHASE_ORDER_PURCHASER_GROUP',
      state: ''
    }
  ];
  for (const set of settings) {
    await setSettingAPI(page, set.key, set.state);
  }
}

/**
 * Creating a new Purchase Order for each test
 * Orders cannot roll back state after being issued.
 * To prevent problems, every test uses its own PO.
 */
test.beforeEach(async ({ page }: { page: Page }) => {
  await doQuickLogin(page, 'admin', 'inventree');

  const cookies = await page.context().cookies();

  for (const cookie of cookies) {
    if (cookie.name === 'csrftoken') {
      TOKEN = cookie.value;
      break;
    }
  }

  const order = await page.request.post('http://localhost:8000/api/order/po/', {
    data: {
      supplier: 1
    },
    headers: {
      'x-csrftoken': TOKEN
    }
  });
  expect(order.ok()).toBeTruthy();
  const pk = (await order.json()).pk;
  ORDER_ID = pk;

  await page.goto(`${baseUrl}/purchasing/purchase-order/${pk}/`, {
    waitUntil: 'domcontentloaded'
  });
  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();
});

/**
 * Log in as admin and disable all settings that were changed.
 */
test.afterEach(async ({ page }: { page: Page }) => {
  await updateToken(page);
  await disableAllSettings(page);
});

test('PUI - Pages - Purchasing - Pending transitions', async ({
  page
}: {
  page: Page;
}) => {
  // Get URL of PO generated before test
  const url = page.url();

  // All state altering settings disabled
  await expect(page.getByRole('button', { name: 'Issue Order' })).toBeEnabled();
  await page.getByRole('button', { name: 'Issue Order' }).click();
  await expect(page.getByRole('button', { name: 'Submit' })).toBeEnabled();

  // Enable Ready Setting
  await toggleReady(page);

  // Check that Ready Button is present
  await page.reload();
  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();

  await expect(page.getByRole('button', { name: 'Ready' })).toBeEnabled();
  await page.getByRole('button', { name: 'Ready' }).click();
  await expect(page.getByRole('button', { name: 'Submit' })).toBeEnabled();

  // Enable Approvals (Approvals come before Ready, so Ready is not disabled)
  await toggleApprovals(page);

  await page.reload();
  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();

  await expect(
    page.getByRole('button', { name: 'Request Approval' })
  ).toBeEnabled();
  await page.getByRole('button', { name: 'Request Approval' }).click();
  await expect(page.getByRole('button', { name: 'Submit' })).toBeEnabled();
});

test('PUI - Pages - Purchasing - In Approval transitions', async ({
  page
}: {
  page: Page;
}) => {
  const url = page.url();

  // Activate Approvals and set  valid approver to not be the current user
  await toggleApprovals(page);
  await setApprover(page, 'readers');

  // Perform state transition through API
  const response = await page.request.post(
    `http://localhost:8000/api/order/po/${ORDER_ID}/request_approval/`,
    {
      headers: {
        'x-csrftoken': TOKEN
      }
    }
  );
  expect(response.ok()).toBeTruthy();

  await page.reload();
  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();

  await expect(page.getByRole('button', { name: 'Approve' })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Recall' })).toBeEnabled();
  await page.getByRole('button', { name: 'Recall' }).click();

  const modal = page.getByRole('dialog');
  await modal.waitFor();
  await modal.getByText('Recall Purchase Order').isVisible();
  await modal.getByRole('button', { name: 'Submit' }).isEnabled();

  // Change approver group to one that user is member of
  await setApprover(page);

  await doLogin(page);

  // Check buttons when the user is permitted to approve
  await page.goto(url);

  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();
  await expect(page.getByRole('button', { name: 'Approve' })).toBeEnabled();
  await page.getByRole('button', { name: 'Approve' }).click();
  await modal.waitFor();
  await expect(modal.getByText('Approve Purchase Order')).toBeVisible();
  await expect(modal.getByRole('button', { name: 'Submit' })).toBeEnabled();
  await modal.getByRole('button', { name: 'Cancel' }).click();
  await expect(page.getByRole('button', { name: 'Reject' })).toBeEnabled();
  await page.getByRole('button', { name: 'Reject' }).click();
  await modal.waitFor();
  await expect(modal.getByLabel('Reject Reason')).toBeVisible();
  await doLogin(page, 'admin', 'inventree');
  await updateToken(page);
});

test('PUI - Pages - Purchasing - Ready Transitions', async ({
  page
}: {
  page: Page;
}) => {
  // Get URL of PO generated before test
  const url = page.url();

  // Standard modal locator
  const modal = page.getByRole('dialog');

  // Activate Ready state
  await toggleReady(page);

  // Perform state transition through API
  const response = await page.request.post(
    `http://localhost:8000/api/order/po/${ORDER_ID}/ready/`,
    {
      headers: {
        'x-csrftoken': TOKEN
      }
    }
  );
  expect(response.ok()).toBeTruthy();

  await page.reload();
  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();

  await expect(page.getByRole('button', { name: 'Issue Order' })).toBeEnabled();
  await expect(page.getByRole('button', { name: 'Recall' })).toBeEnabled();
  await page.getByRole('button', { name: 'Recall' }).click();

  await modal.waitFor();
  await expect(modal.getByText('Recall Purchase Order')).toBeVisible();
  await expect(modal.getByRole('button', { name: 'Submit' })).toBeEnabled();
  await modal.getByRole('button', { name: 'Cancel' }).click();

  await page.getByRole('button', { name: 'Issue Order' }).click();

  await modal.waitFor();
  await expect(modal.getByText('Issue Order')).toBeVisible();
  await expect(modal.getByRole('button', { name: 'Submit' })).toBeEnabled();

  await setPurchaser(page, 'readers');
  await toggleReady(page);

  await page.reload();
  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();
  await expect(
    page.getByRole('button', { name: 'Issue Order' })
  ).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Recall' })).toBeEnabled();
});

test('PUI - Pages - Purchasing - Placed Transitions', async ({
  page
}: {
  page: Page;
}) => {
  const url = page.url();

  const modal = page.getByRole('dialog');

  // Perform state transition through API
  const response = await page.request.post(
    `http://localhost:8000/api/order/po/${ORDER_ID}/issue/`,
    {
      headers: {
        'x-csrftoken': TOKEN
      }
    }
  );
  expect(response.ok()).toBeTruthy();

  await page.reload();
  await page.getByRole('button', { name: 'Complete' }).waitFor();
  await page.getByRole('button', { name: 'Complete' }).click();
  await expect(modal.getByText('Complete Purchase Order')).toBeVisible();
  await expect(
    modal.getByText('All line items have been received')
  ).toBeVisible();
  await modal.getByRole('button', { name: 'Cancel' }).click();
});
