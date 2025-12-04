import { test } from '../baseFixtures.js';
import { clickOnParamFilter, loadTab, navigate } from '../helpers.js';
import { doCachedLogin } from '../login.js';

test('Company', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await navigate(page, 'company/1/details');
  await page.getByLabel('Details').getByText('DigiKey Electronics').waitFor();
  await page.getByRole('cell', { name: 'https://www.digikey.com/' }).waitFor();
  await loadTab(page, 'Supplied Parts');
  await page
    .getByRole('cell', { name: 'RR05P100KDTR-ND', exact: true })
    .waitFor();
  await loadTab(page, 'Purchase Orders');
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
  await page.getByLabel('action-menu-company-actions').click();
  await page.getByLabel('action-menu-company-actions-edit').click();

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
    username: 'steven',
    password: 'wizardstaff',
    url: 'purchasing/index/suppliers'
  });

  // Show parametric view
  await page
    .getByRole('button', { name: 'segmented-icon-control-parametric' })
    .click();

  // Filter by "payment terms" parameter value
  await clickOnParamFilter(page, 'Payment Terms');
  await page.getByRole('option', { name: 'NET-30' }).click();

  await page.getByRole('cell', { name: 'Arrow Electronics' }).waitFor();
  await page.getByRole('cell', { name: 'PCB assembly house' }).waitFor();
});
