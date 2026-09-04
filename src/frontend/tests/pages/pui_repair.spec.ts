import { test } from '../baseFixtures';
import { loadTab, navigate } from '../helpers';
import { doCachedLogin } from '../login';
import { setSettingState } from '../settings';

test('Repair Orders - Basic Navigation', async ({ browser }) => {
  // Enable the feature flag BEFORE opening the page
  await setSettingState({ setting: 'REPAIRORDER_ENABLED', value: true });

  // Log in and navigate to the manufacturing index (not directly to repairorders)
  const page = await doCachedLogin(browser);

  // Navigate to the manufacturing page — the fresh navigation ensures settings are loaded
  await navigate(page, 'manufacturing/index/');
  await page.waitForURL('**/manufacturing/index/**');

  // Verify the Repair Orders tab is visible and click it
  await page.getByRole('tab', { name: 'Repair Orders' }).waitFor();
  await page.getByRole('tab', { name: 'Repair Orders' }).click();
});

test('Repair Orders - Create and Lifecycle', async ({ browser }) => {
  // Enable the feature flag BEFORE opening the page
  await setSettingState({ setting: 'REPAIRORDER_ENABLED', value: true });

  // Log in and navigate to the manufacturing index
  const page = await doCachedLogin(browser);

  await navigate(page, 'manufacturing/index/');
  await page.waitForURL('**/manufacturing/index/**');

  // Click the Repair Orders tab to switch to the repair orders view
  await page.getByRole('tab', { name: 'Repair Orders' }).click();

  // Click the "Add Repair Order" button
  await page.getByLabel('action-button-add-repair-order').click();

  // Fill out the creation form - part is required
  await page.getByLabel('related-field-part').fill('MAST');
  await page.getByText('MAST | Master Assembly').click();

  await page.getByLabel('text-field-description').fill('E2E Test Repair Order');
  await page.getByRole('button', { name: 'Submit' }).click();

  // Wait for navigation to the detail page
  await page.getByText('E2E Test Repair Order').waitFor();

  // Verify the status shows "Pending"
  await page.getByText('Pending').waitFor();

  // Navigate through tabs
  await loadTab(page, 'Line Items');
  await loadTab(page, 'Attachments');
  await loadTab(page, 'Notes');
});
