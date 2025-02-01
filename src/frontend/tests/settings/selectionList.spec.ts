import { test } from '../baseFixtures';
import { navigate } from '../helpers';
import { doQuickLogin } from '../login';

test('PUI - Admin - Parameter', async ({ page }) => {
  await doQuickLogin(page, 'admin', 'inventree');
  await page.getByRole('button', { name: 'admin' }).click();
  await page.getByRole('menuitem', { name: 'Admin Center' }).click();
  await page.getByRole('tab', { name: 'Part Parameters' }).click();

  await page.getByRole('button', { name: 'Selection Lists' }).click();
  await page.waitForLoadState('networkidle');

  // clean old data if exists
  await page
    .getByRole('cell', { name: 'some list' })
    .waitFor({ timeout: 200 })
    .then(async (cell) => {
      await page
        .getByRole('cell', { name: 'some list' })
        .locator('..')
        .getByLabel('row-action-menu-')
        .click();
      await page.getByRole('menuitem', { name: 'Delete' }).click();
      await page.getByRole('button', { name: 'Delete' }).click();
    })
    .catch(() => {});

  // clean old data if exists
  await page.getByRole('button', { name: 'Part Parameter Template' }).click();
  await page.waitForLoadState('networkidle');
  await page
    .getByRole('cell', { name: 'my custom parameter' })
    .waitFor({ timeout: 200 })
    .then(async (cell) => {
      await page
        .getByRole('cell', { name: 'my custom parameter' })
        .locator('..')
        .getByLabel('row-action-menu-')
        .click();
      await page.getByRole('menuitem', { name: 'Delete' }).click();
      await page.getByRole('button', { name: 'Delete' }).click();
    })
    .catch(() => {});

  // Add selection list
  await page.getByRole('button', { name: 'Selection Lists' }).click();
  await page.waitForLoadState('networkidle');
  await page.getByLabel('action-button-add-selection-').waitFor();
  await page.getByLabel('action-button-add-selection-').click();
  await page.getByLabel('text-field-name').fill('some list');
  await page.getByLabel('text-field-description').fill('Listdescription');
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByRole('cell', { name: 'some list' }).waitFor();
  await page.waitForTimeout(200);

  // Add parameter
  await page.waitForLoadState('networkidle');
  await page.getByRole('button', { name: 'Part Parameter Template' }).click();
  await page.getByLabel('action-button-add-parameter').waitFor();
  await page.getByLabel('action-button-add-parameter').click();
  await page.getByLabel('text-field-name').fill('my custom parameter');
  await page.getByLabel('text-field-description').fill('description');
  await page
    .locator('div')
    .filter({ hasText: /^Search\.\.\.$/ })
    .nth(2)
    .click();
  await page
    .getByRole('option', { name: 'some list' })
    .locator('div')
    .first()
    .click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByRole('cell', { name: 'my custom parameter' }).click();

  // Fill parameter
  await navigate(page, 'part/104/parameters/');
  await page.getByLabel('Parameters').getByText('Parameters').waitFor();
  await page.waitForLoadState('networkidle');
  await page.getByLabel('action-button-add-parameter').waitFor();
  await page.getByLabel('action-button-add-parameter').click();
  await page.waitForTimeout(200);
  await page.getByText('New Part Parameter').waitFor();
  await page
    .getByText('Template *Parameter')
    .locator('div')
    .filter({ hasText: /^Search\.\.\.$/ })
    .nth(2)
    .click();
  await page
    .getByText('Template *Parameter')
    .locator('div')
    .filter({ hasText: /^Search\.\.\.$/ })
    .locator('input')
    .fill('my custom parameter');
  await page.getByRole('option', { name: 'my custom parameter' }).click();
  await page.getByLabel('choice-field-data').fill('2');
  await page.getByRole('button', { name: 'Submit' }).click();
});
