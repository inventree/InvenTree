import { APIRequestContext, Page } from '@playwright/test';

import { expect, test } from '../baseFixtures';
import { adminuser, baseUrl, user } from '../defaults';
import { doLogin, doQuickLogin } from '../login';

// CSRF token
let TOKEN: string;

// These tests modify settings, and have to run sequentially
// Each test will reset settings with its afterEach hook
test.describe.configure({ mode: 'serial' });

async function setting(
  request: APIRequestContext,
  key: string,
  value: string | boolean | null
) {
  const settingResponse = await request.patch(
    `http://localhost:8000/api/settings/global/${key}/`,
    {
      data: {
        value: value
      },
      headers: {
        Authorization: TOKEN
      }
    }
  );
  expect(settingResponse.ok()).toBeTruthy();
  return;
}

async function toggleReady(request: APIRequestContext, disable = false) {
  await setting(request, 'ENABLE_PURCHASE_ORDER_READY_STATUS', !disable);
}

async function toggleApprovals(request: APIRequestContext, disable = false) {
  await setting(request, 'ENABLE_PURCHASE_ORDER_APPROVAL', !disable);
}

async function setApprover(request: APIRequestContext, group = 'all access') {
  await setting(request, 'PURCHASE_ORDER_APPROVE_ALL_GROUP', group);
}

async function setPurchaser(request: APIRequestContext, group = 'all access') {
  await setting(request, 'PURCHASE_ORDER_PURCHASER_GROUP', group);
}

async function disableAllSettings(request: APIRequestContext) {
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
    await setting(request, set.key, set.state);
  }
}

test.beforeAll(async ({ request }: { request: APIRequestContext }) => {
  const login = await request.post(`http://localhost:8000/api/auth/login/`, {
    data: {
      username: 'admin',
      password: 'inventree'
    }
  });
  expect(login.ok()).toBeTruthy();
  TOKEN = `Token ${(await login.json()).key}`;
});

/**
 * Creating a new Purchase Order for each test
 * Orders cannot roll back state after being issued.
 * To prevent problems, every test uses its own PO.
 */
test.beforeEach(
  async ({ page, request }: { page: Page; request: APIRequestContext }) => {
    const order = await request.post('http://localhost:8000/api/order/po/', {
      data: {
        supplier: 1
      },
      headers: {
        Authorization: TOKEN
      }
    });
    expect(order.ok()).toBeTruthy();
    await doQuickLogin(page);
    const pk = (await order.json()).pk;
    await page.goto(`${baseUrl}/purchasing/purchase-order/${pk}/`);
    await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();
  }
);

/**
 * Log in as admin and disable all settings that were changed.
 */
test.afterEach(async ({ request }: { request: APIRequestContext }) => {
  await disableAllSettings(request);
});

test('PUI - Pages - Purchasing - Pending transitions', async ({
  page,
  request
}: {
  page: Page;
  request: APIRequestContext;
}) => {
  // Get URL of PO generated before test
  const url = page.url();

  // All state altering settings disabled
  await expect(page.getByRole('button', { name: 'Issue Order' })).toBeEnabled();
  await page.getByRole('button', { name: 'Issue Order' }).click();
  await expect(page.getByRole('button', { name: 'Submit' })).toBeEnabled();

  // Enable Ready Setting
  await toggleReady(request);

  // Check that Ready Button is present
  await page.goto(url);
  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();
  await page.getByRole('button', { name: 'Ready' }).isEnabled();
  await page.getByRole('button', { name: 'Ready' }).click();
  await page.getByRole('button', { name: 'Submit' }).isEnabled();

  // Enable Approvals (Approvals come before Ready, so Ready is not disabled)
  await toggleApprovals(request);

  await page.goto(url);
  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();
  await page.getByRole('button', { name: 'Request Approval' }).isEnabled();
  await page.getByRole('button', { name: 'Request Approval' }).click();
  await page.getByRole('button', { name: 'Submit' }).isEnabled();
});

test('PUI - Pages - Purchasing - In Approval transitions', async ({
  page,
  request
}: {
  page: Page;
  request: APIRequestContext;
}) => {
  const url = page.url();
  await toggleApprovals(request);
  await setApprover(request, 'readers');

  await page.goto(url);
  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();
  await page.getByRole('button', { name: 'Request Approval' }).click();

  const modal = page.getByRole('dialog');
  await modal.getByRole('button', { name: 'Submit' }).click();

  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();
  await page.getByRole('button', { name: 'Approve' }).waitFor();
  await page.getByRole('button', { name: 'Approve' }).isDisabled();
  await page.getByRole('button', { name: 'Recall' }).isEnabled();
  await page.getByRole('button', { name: 'Recall' }).click();

  await modal.waitFor();
  await modal.getByText('Recall Purchase Order').isVisible();
  await modal.getByRole('button', { name: 'Submit' }).isEnabled();

  await setApprover(request);

  await page.reload();
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

test('PUI - Pages - Purchasing - Ready Transitions', async ({
  page,
  request
}: {
  page: Page;
  request: APIRequestContext;
}) => {
  // Get URL of PO generated before test
  const url = page.url();

  // Standard modal locator
  const modal = page.getByRole('dialog');

  await toggleReady(request);

  await page.goto(url);
  await page.getByText(RegExp(/^Purchase Order: PO\d{4}$/)).waitFor();
  await expect(page.getByRole('button', { name: 'Ready' })).toBeEnabled();
  await page.getByRole('button', { name: 'Ready' }).click();

  await modal.getByRole('button', { name: 'Submit' }).click();

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

  await setPurchaser(request, 'readers');

  await page.goto(url);
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

  await page.getByRole('button', { name: 'Issue Order' }).click();
  await modal.waitFor();
  expect(modal.getByRole('button', { name: 'Submit' })).toBeEnabled();
  await modal.getByRole('button', { name: 'Submit' }).click();

  await page.getByRole('button', { name: 'Complete' }).waitFor();
  await page.getByRole('button', { name: 'Complete' }).click();
  await expect(modal.getByText('Complete Purchase Order')).toBeVisible();
  await expect(
    modal.getByText('All line items have been received')
  ).toBeVisible();
  await modal.getByRole('button', { name: 'Cancel' }).click();
});
