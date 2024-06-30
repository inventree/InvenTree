import { test } from '../baseFixtures';
import { adminuser, baseUrl } from '../defaults';
import { doLogin, doQuickLogin } from '../login';

test('PUI - Pages - Purchasing - Detail', async ({ page }) => {
  await doQuickLogin(page);

  // All state altering settings disabled
  await page.goto(`${baseUrl}/purchasing/purchase-order/12/detail`);
  await page.getByText('PO0012').waitFor();
  await page.getByRole('button', { name: 'Issue Order' }).isEnabled();

  // Enable Ready setting
  await doLogin(page, adminuser.username, adminuser.password);
  await page.goto(`${baseUrl}/settings/system/purchaseorders`);
  await page.getByText('Enable Ready Status').waitFor();
  await page
    .locator('div', { hasText: 'Enable Ready Status' })
    .getByRole('switch')
    .click();

  await doLogin(page);
  await page.goto(`${baseUrl}/purchasing/purchase-order/12/detail`);
  await page.getByText('PO0012').waitFor();
  await page.getByRole('button', { name: 'Ready' }).isEnabled();
});
