import { test } from '../baseFixtures.ts';
import { baseUrl } from '../defaults.ts';
import { doQuickLogin } from '../login.ts';

test('PUI - Sales Orders', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/home`);
  await page.getByRole('tab', { name: 'Sales' }).click();
  await page.getByRole('tab', { name: 'Sales Orders' }).click();

  // Check for expected text in the table
  await page.getByRole('tab', { name: 'Sales Orders' }).waitFor();
  await page.getByText('In Progress').first().waitFor();
  await page.getByText('On Hold').first().waitFor();

  // Navigate to a particular sales order
  await page.getByRole('cell', { name: 'SO0003' }).click();

  // Order is "on hold". We will "issue" it and then place on hold again
  await page.getByText('Sales Order: SO0003').waitFor();
  await page.getByText('On Hold').first().waitFor();
  await page.getByRole('button', { name: 'Issue Order' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();

  // Order should now be "in progress"
  await page.getByText('In Progress').first().waitFor();
  await page.getByRole('button', { name: 'Ship Order' }).waitFor();

  await page.getByLabel('action-menu-order-actions').click();

  await page.getByLabel('action-menu-order-actions-edit').waitFor();
  await page.getByLabel('action-menu-order-actions-duplicate').waitFor();
  await page.getByLabel('action-menu-order-actions-cancel').waitFor();

  // Mark the order as "on hold" again
  await page.getByLabel('action-menu-order-actions-hold').click();
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('On Hold').first().waitFor();
  await page.getByRole('button', { name: 'Issue Order' }).waitFor();
});
