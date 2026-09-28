import { test } from '../baseFixtures';
import { loadTab } from '../helpers';
import { doCachedLogin } from '../login';
import { setSettingState } from '../settings';

test('Repair Orders - Basic Navigation', async ({ browser }) => {
  // Enable the feature flag BEFORE opening the page so the React app
  // receives the correct setting on its very first settings fetch.
  await setSettingState({ setting: 'REPAIRORDER_ENABLED', value: true });

  // Navigate directly to the manufacturing index during login so the page
  // loads with the already-patched setting from a fresh network request.
  const page = await doCachedLogin(browser, {
    url: 'manufacturing/index/'
  });

  // Wait for the page to be fully settled before probing tabs.
  await page.waitForLoadState('networkidle');

  // Use the loadTab helper (queries by ARIA label 'panel-tabs-*') which is
  // consistent with other index-page tests (e.g. pui_build.spec.ts).
  await loadTab(page, 'Repair Orders');
});

test('Repair Orders - Create and Lifecycle', async ({ browser }) => {
  // Enable the feature flag BEFORE opening the page.
  await setSettingState({ setting: 'REPAIRORDER_ENABLED', value: true });

  // Navigate directly to the manufacturing index during login.
  const page = await doCachedLogin(browser, {
    url: 'manufacturing/index/'
  });

  await page.waitForLoadState('networkidle');

  // Switch to the Repair Orders panel.
  await loadTab(page, 'Repair Orders');

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
