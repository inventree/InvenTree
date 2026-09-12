import { test } from '../baseFixtures';
import { loadTab, navigate } from '../helpers';
import { doCachedLogin } from '../login';
import { setSettingState } from '../settings';

test('Repair Orders - Basic Navigation', async ({ browser }) => {
  // Enable the feature flag BEFORE opening the page
  await setSettingState({ setting: 'REPAIRORDER_ENABLED', value: true });

  // Log in and navigate directly to the repairorders sub-panel path
  // This avoids the race condition where the tab may not be visible yet
  const page = await doCachedLogin(browser);

  // Navigate directly to the repairorders panel URL
  await navigate(page, 'manufacturing/index/repairorders');

  // Reload to ensure the global settings state is fully hydrated in React
  await page.reload();
  await page.waitForLoadState('networkidle');

  // Verify the Repair Orders tab is now visible and selected
  await page.getByRole('tab', { name: 'Repair Orders' }).waitFor();
  await page.getByRole('tab', { name: 'Repair Orders' }).click();
});

test('Repair Orders - Create and Lifecycle', async ({ browser }) => {
  // Enable the feature flag BEFORE opening the page
  await setSettingState({ setting: 'REPAIRORDER_ENABLED', value: true });

  // Log in and navigate directly to the repairorders panel
  const page = await doCachedLogin(browser);

  await navigate(page, 'manufacturing/index/repairorders');

  // Reload to ensure settings are fully hydrated
  await page.reload();
  await page.waitForLoadState('networkidle');

  // The Repair Orders tab should now be visible and active
  await page.getByRole('tab', { name: 'Repair Orders' }).waitFor();
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
