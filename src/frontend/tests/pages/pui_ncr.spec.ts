import { test } from '../baseFixtures.js';
import { adminuser } from '../defaults.js';
import { clickOnRowMenu, loadTab, navigate } from '../helpers.js';
import { doCachedLogin } from '../login.js';
import { setSettingState } from '../settings.js';

// Note: The 'admin' user is used here, as the demo dataset does not
// assign the 'ncr' role to any of the other test user groups

test('NCR - Visibility', async ({ browser }) => {
  // With NCR disabled, the panel should not be available
  await setSettingState({ setting: 'NCR_ENABLED', value: false });

  const page = await doCachedLogin(browser, {
    user: adminuser,
    url: 'manufacturing/index/'
  });

  await page.getByRole('tab', { name: 'Build Orders' }).waitFor();
  await page.getByRole('tab', { name: 'Non-Conformances' }).waitFor({
    state: 'hidden'
  });

  // Enable NCR, and reload the page
  await setSettingState({ setting: 'NCR_ENABLED', value: true });

  await navigate(page, 'manufacturing/index/');
  await page.reload();

  await page.getByRole('tab', { name: 'Manufacturing' }).waitFor();
  await loadTab(page, 'Non-Conformances');
  await page
    .getByRole('button', { name: 'action-button-report-non-conformance' })
    .waitFor();
});

test('NCR - Workflow', async ({ browser }) => {
  await setSettingState({ setting: 'NCR_ENABLED', value: true });

  const page = await doCachedLogin(browser, {
    user: adminuser,
    url: 'manufacturing/index/ncr'
  });

  // Raise a new NCR
  await page
    .getByRole('button', { name: 'action-button-report-non-conformance' })
    .click();

  await page.getByLabel('related-field-part').fill('Blue Chair');
  await page
    .getByRole('option', { name: /Blue Chair/ })
    .first()
    .click();

  await page
    .getByLabel('text-field-description', { exact: true })
    .fill('Paint defect found during inspection');

  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Item Created').waitFor();

  // We should now be on the NCR detail page
  await page.waitForURL('**/manufacturing/ncr/**');
  await page.getByText('Pending').first().waitFor();

  // Link a stock item
  await loadTab(page, 'Stock Items');
  await page
    .getByRole('button', { name: 'action-button-link-stock-item' })
    .click();
  await page.getByLabel('related-field-stock_item').click();
  await page.getByRole('option').first().click();
  await page.getByRole('button', { name: 'Submit' }).click();

  // Try to complete the NCR - should fail, disposition is still pending
  await page.getByRole('button', { name: 'Complete' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page
    .getByText('All linked stock items must be assigned a disposition')
    .waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Investigate the NCR
  await page.getByRole('button', { name: 'Investigate' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('NCR is now under investigation').waitFor();
  await page.getByText('In Progress').first().waitFor();

  // Assign a disposition to the linked stock item
  const cell = page.getByRole('cell', { name: 'Pending' });
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await page.getByLabel('choice-field-disposition').click();
  await page.getByRole('option', { name: 'Scrap' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByRole('cell', { name: 'Scrap' }).waitFor();

  // Now the NCR can be completed
  await page.getByRole('button', { name: 'Complete' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('NCR completed').waitFor();
  await page.getByText('Complete').first().waitFor();

  // Transition actions are no longer available
  await page
    .getByRole('button', { name: 'Investigate' })
    .waitFor({ state: 'hidden' });

  // Check the other panels load
  await loadTab(page, 'Attachments');
  await loadTab(page, 'Notes');
});
