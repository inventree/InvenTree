import { test } from '../baseFixtures';
import { doQuickLogin } from '../login';

test('PUI - Admin - Parameter', async ({ page }) => {
  await doQuickLogin(page, 'admin', 'inventree');
  await page.getByRole('button', { name: 'admin' }).click();
  await page.getByRole('menuitem', { name: 'Admin Center' }).click();

  await page.getByRole('tab', { name: 'Part Parameters' }).click();
  await page.getByLabel('action-button-add-parameter-').click();
  await page.getByLabel('text-field-name').click();
  await page.getByLabel('text-field-name').fill('my custom parameter');
  await page.getByLabel('text-field-description').click();
  await page.getByLabel('text-field-description').fill('description');
  await page
    .locator('div')
    .filter({ hasText: /^Search\.\.\.$/ })
    .nth(2)
    .click();
  await page
    .getByRole('option', { name: 'some list List with some' })
    .locator('div')
    .first()
    .click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByRole('cell', { name: 'my custom parameter' }).click();
});
