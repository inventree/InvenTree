import { test } from '../baseFixtures';
import { loadTab } from '../helpers';
import { doCachedLogin } from '../login';

test('Repair Orders - Basic Navigation', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'manufacturing/index/repairorders'
  });

  // Verify the Repair Orders panel is visible
  await page.getByRole('tab', { name: 'Repair Orders' }).waitFor();
});

test('Repair Orders - Create and Lifecycle', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'manufacturing/index/repairorders'
  });

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
