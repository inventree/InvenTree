import { expect } from '@playwright/test';
import { test } from '../baseFixtures';
import {
  clearTableFilters,
  loadTab,
  showParametricView,
  tableSearch
} from '../helpers';
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

test('Return Orders - Parametric View', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'sales/index/returnorders'
  });

  await showParametricView(page);
  await clearTableFilters(page);

  // Columns and data are rendered in the parametric table
  await page.getByRole('button', { name: 'Customer' }).waitFor();
  await page.getByRole('cell', { name: 'RMA-0002' }).waitFor();

  // Search within the parametric table
  await tableSearch(page, 'RMA-0002');
  await page.getByRole('cell', { name: 'RMA-0002' }).waitFor();
  await expect(page.getByRole('cell', { name: 'RMA-0001' })).toHaveCount(0);
});
