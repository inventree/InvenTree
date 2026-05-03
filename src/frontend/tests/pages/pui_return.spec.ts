import test from '@playwright/test';
import { loadTab } from '../helpers';
import { doCachedLogin } from '../login';

test('Return Orders - Receive Items', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'sales/index/returnorders'
  });

  await page.getByRole('cell', { name: 'RMA-0002' }).click();
  await loadTab(page, 'Parameters');
  await loadTab(page, 'Attachments');
  await loadTab(page, 'Line Items');

  await page.getByRole('checkbox', { name: 'Select all records' }).click();
  await page.getByRole('button', { name: 'action-button-receive-' }).click();
  await page.getByRole('banner').getByText('Receive Items').waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();
});
