import type { Browser, Page } from '@playwright/test';
import { test } from '../baseFixtures';
import { adminuser } from '../defaults';
import { loadTab } from '../helpers';
import { doCachedLogin } from '../login';
import { setSettingState } from '../settings';

const refreshSettings = async (page: Page) => {
  const settingsResponse = page.waitForResponse(
    (response) =>
      response.url().includes('/api/settings/global/') &&
      response.request().method() === 'GET' &&
      response.ok()
  );

  await page.reload();
  await settingsResponse;
  await page.waitForLoadState('networkidle');
};

const openRepairOrders = async (browser: Browser) => {
  const page = await doCachedLogin(browser, {
    // The test fixture does not automatically grant newly introduced roles
    // to allaccess. Use the admin fixture to satisfy the repair_order gate.
    user: adminuser,
    url: 'manufacturing/index/'
  });

  await refreshSettings(page);
  await loadTab(page, 'Repair Orders');

  return page;
};

test.beforeEach(async () => {
  await setSettingState({ setting: 'REPAIRORDER_ENABLED', value: true });
});

test.afterEach(async () => {
  await setSettingState({ setting: 'REPAIRORDER_ENABLED', value: false });
});

test('Repair Orders - Basic Navigation', async ({ browser }) => {
  await openRepairOrders(browser);
});

test('Repair Orders - Create and Lifecycle', async ({ browser }) => {
  const page = await openRepairOrders(browser);

  // Click the "Add Repair Order" action button.
  await page.getByLabel('action-button-add-repair-order').click();

  // Fill out the creation form – part is a required field.
  await page.getByLabel('related-field-part').fill('MAST');
  await page.getByText('MAST | Master Assembly').click();

  await page.getByLabel('text-field-description').fill('E2E Test Repair Order');
  await page.getByRole('button', { name: 'Submit' }).click();

  // Wait for navigation to the newly-created detail page.
  await page.getByText('E2E Test Repair Order').waitFor();

  // Verify the initial status shows "Pending".
  await page.getByText('Pending').waitFor();

  // Navigate through the detail-page tabs.
  await loadTab(page, 'Line Items');
  await loadTab(page, 'Attachments');
  await loadTab(page, 'Notes');
});
