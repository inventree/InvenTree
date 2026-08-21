import { test } from '../baseFixtures.js';
import { stevenuser } from '../defaults.js';
import {
  clearTableFilters,
  clickOnParamFilter,
  loadTab,
  navigate,
  openDetailAction,
  setTableChoiceFilter,
  showParametricView
} from '../helpers.js';
import { doCachedLogin } from '../login.js';

test('Company - Basic Tests', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await navigate(page, 'company/1/details');
  await page.getByLabel('Details').getByText('DigiKey Electronics').waitFor();
  await page.getByRole('cell', { name: 'https://www.digikey.com/' }).waitFor();

  await loadTab(page, 'Supplied Parts');
  await page
    .getByRole('cell', { name: 'RR05P100KDTR-ND', exact: true })
    .waitFor();

  await loadTab(page, 'Purchase Orders');
  await clearTableFilters(page);
  await page.getByRole('cell', { name: 'Molex connectors' }).first().waitFor();

  await loadTab(page, 'Stock Items');
  await page
    .getByRole('cell', { name: 'Blue plastic enclosure' })
    .first()
    .waitFor();

  await loadTab(page, 'Contacts');
  await page.getByRole('cell', { name: 'jimmy.mcleod@digikey.com' }).waitFor();

  await loadTab(page, 'Addresses');
  await page.getByRole('cell', { name: 'Carla Tunnel' }).waitFor();

  await loadTab(page, 'Attachments');
  await loadTab(page, 'Notes');

  // Let's edit the company details
  await openDetailAction(page, 'company', 'edit');

  await page.getByLabel('text-field-name', { exact: true }).fill('');
  await page
    .getByLabel('text-field-website', { exact: true })
    .fill('invalid-website');
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('This field may not be blank.').waitFor();
  await page.getByText('Enter a valid URL.').waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();
});

test('Company - Parameters', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    user: stevenuser,
    url: 'purchasing/index/suppliers'
  });

  // Show parametric view
  await showParametricView(page);

  // Filter by "payment terms" parameter value
  await clickOnParamFilter(page, 'Payment Terms');
  await page.getByRole('option', { name: 'NET-30' }).click();

  await page.getByRole('cell', { name: 'Arrow Electronics' }).waitFor();
  await page.getByRole('cell', { name: 'SUP-012' }).waitFor();

  await page.getByRole('cell', { name: 'PCBA+' }).click();
  await page.getByRole('link', { name: 'details-company-45' }).click();

  // Let's duplicate this company
  await openDetailAction(page, 'company', 'duplicate');
  await page
    .getByRole('textbox', { name: 'text-field-name' })
    .fill(`PCBA Duplicate ${Math.floor(Math.random() * 1000)}`);
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.waitForLoadState('networkidle');
  await loadTab(page, 'Parameters');

  // Only one parameter should be visible (unique parameters not copied)
  await page.getByRole('cell', { name: 'NET-30' }).waitFor();
  await page.getByText('1 - 1 / 1').waitFor();

  // Try to create a duplicate parameter
  await page
    .getByRole('button', { name: 'action-menu-add-parameters' })
    .click();
  await page
    .getByRole('menuitem', {
      name: 'action-menu-add-parameters-create-parameter'
    })
    .click();

  await page
    .getByRole('combobox', { name: 'related-field-template' })
    .fill('supplier');
  await page.getByRole('option', { name: 'Supplier ID' }).click();

  await page.getByRole('textbox', { name: 'text-field-data' }).fill('SUP-012');
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Parameter value must be unique').waitFor();
});

test('Company - Supplier Parts', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    user: stevenuser,
    url: 'purchasing/index/suppliers'
  });

  await loadTab(page, 'Supplier Parts');
  await clearTableFilters(page);
  await page.getByText(/1 \- 25 \/ 7\d\d/).waitFor();

  await setTableChoiceFilter(page, 'Primary', 'Yes');
  await page.getByText(/1 \- 25 \/ 3\d\d/).waitFor();

  await clearTableFilters(page);
  await setTableChoiceFilter(page, 'Primary', 'No');
  await page.getByText(/1 \- 25 \/ 4\d\d/).waitFor();
});
