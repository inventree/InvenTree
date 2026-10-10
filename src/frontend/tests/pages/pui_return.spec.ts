import { expect } from '@playwright/test';
import { test } from '../baseFixtures';
import { loadTab } from '../helpers';
import { doCachedLogin } from '../login';

test('Return Orders - Receive Items', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'sales/index/returnorders'
  });

  await page.getByRole('cell', { name: 'RMA-0002' }).click();

  // Creator of the order should be displayed
  await expect(page.getByRole('row', { name: 'Created By' })).toContainText(
    'admin'
  );

  await loadTab(page, 'Parameters');
  await loadTab(page, 'Attachments');
  await loadTab(page, 'Line Items');

  await page.getByRole('cell', { name: 'WID-REV-A' }).first().waitFor();

  await page
    .getByRole('region', { name: 'Line Items', exact: true })
    .getByLabel('Select all records')
    .click();
  await page.getByRole('button', { name: 'action-button-receive-' }).click();
  await page.getByRole('banner').getByText('Receive Items').waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();
});
