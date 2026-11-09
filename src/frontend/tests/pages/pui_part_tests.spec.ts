/**
 * Tests for the "Test Templates" panel on the part detail page
 */

import { createApi } from '../api.js';
import { expect, generateUUID, test } from '../baseFixtures.js';
import {
  clearTableFilters,
  clickOnRowMenu,
  loadTab,
  navigate,
  setTableChoiceFilter
} from '../helpers.js';
import { doCachedLogin } from '../login.js';

test('Parts - Test Templates', async ({ browser }) => {
  const testName = `PW Test ${generateUUID().slice(0, 8)}`;

  // "Doohickey" - a testable part with its own test templates
  const page = await doCachedLogin(browser, { url: 'part/87/' });
  await loadTab(page, 'Test Templates');

  // Exercise table filters
  await setTableChoiceFilter(page, 'Required', 'Yes');
  await clearTableFilters(page);
  await setTableChoiceFilter(page, 'Has Results', 'No');
  await clearTableFilters(page);

  // Create a new test template
  await page.getByLabel('action-button-add-test-template').click();
  await page.getByLabel('text-field-test_name').fill(testName);
  await page.getByLabel('text-field-description').fill('Playwright test');
  await page.getByRole('switch', { name: 'boolean-field-required' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();

  const cell = page.getByRole('cell', { name: testName });
  await cell.waitFor();

  // Hover to display template details
  await page.getByText(testName, { exact: true }).hover();

  // Edit the template
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await page.getByLabel('text-field-description').fill('Edited description');
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByRole('cell', { name: 'Edited description' }).waitFor();

  // Delete the template
  await clickOnRowMenu(page.getByRole('cell', { name: testName }));
  await page.getByRole('menuitem', { name: 'Delete' }).click();
  await page.getByText('This action cannot be reversed').waitFor();
  await page.getByRole('button', { name: 'Delete' }).click();
  await expect(page.getByRole('cell', { name: testName })).toHaveCount(0);

  // "Widget Assembly Variant" - inherits tests from "Widget Assembly"
  await navigate(page, 'part/81/');
  await loadTab(page, 'Test Templates');

  const inherited = page.getByText(
    'Test is defined for a parent template part'
  );
  const row = page.locator('table tbody tr').first();
  await row.waitFor();
  await row.locator('td').first().hover();

  if (await inherited.first().isVisible()) {
    await inherited.first().waitFor();
  }

  // Inherited tests only provide a "View Parent Part" action
  await row.getByLabel(/row-action-menu-/i).click();
  await page.getByRole('menuitem', { name: 'View Parent Part' }).click();
  await page.waitForURL('**/part/77/**');
});

test('Parts - Test Templates (Locked)', async ({ browser }) => {
  const api = await createApi({});

  // Ensure part locking is enabled
  await api.patch('settings/global/PART_ENABLE_LOCKING/', {
    data: { value: true }
  });

  // "Test Board 2" - a locked part
  const page = await doCachedLogin(browser, { url: 'part/111/' });
  await loadTab(page, 'Test Templates');
  await page.getByText('Part is Locked', { exact: true }).first().waitFor();
  await page
    .getByText('Part templates cannot be edited, as the part is locked')
    .waitFor();

  await expect(page.getByLabel('action-button-add-test-template')).toHaveCount(
    0
  );
});
