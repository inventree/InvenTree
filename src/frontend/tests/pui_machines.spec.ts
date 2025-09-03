import test from 'playwright/test';
import { clickOnRowMenu, navigate } from './helpers';
import { doCachedLogin } from './login';
import { setPluginState } from './settings';

test('Machines - Admin Panel', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    username: 'admin',
    password: 'inventree',
    url: 'settings/admin/machine'
  });

  await page.getByRole('button', { name: 'Machines' }).click();
  await page.getByRole('button', { name: 'Machine Drivers' }).click();
  await page.getByRole('button', { name: 'Machine Types' }).click();
  await page.getByRole('button', { name: 'Machine Errors' }).click();

  await page.getByText('There are no machine registry errors').waitFor();
});

test('Machines - Activation', async ({ browser, request }) => {
  const page = await doCachedLogin(browser, {
    username: 'admin',
    password: 'inventree',
    url: 'settings/admin/machine'
  });

  // Ensure that the sample machine plugin is enabled
  await setPluginState({
    request,
    plugin: 'sample-printer-machine-plugin',
    state: true
  });

  await page.reload();
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);

  // Create machine config if it does not already exist
  const exists: boolean = await page
    .getByRole('cell', { name: 'my-dummy-machine' })
    .isVisible({ timeout: 250 });

  if (!exists) {
    await page
      .getByRole('button', { name: 'action-button-add-machine' })
      .click();
    await page
      .getByRole('textbox', { name: 'text-field-name' })
      .fill('my-dummy-machine');
    await page
      .getByRole('textbox', { name: 'choice-field-machine_type' })
      .fill('label');
    await page.getByRole('option', { name: 'Label Printer' }).click();

    await page.getByRole('textbox', { name: 'choice-field-driver' }).click();
    await page
      .getByRole('option', { name: 'Sample Label Printer Driver' })
      .click();
    await page.getByRole('button', { name: 'Submit' }).click();
  } else {
    // Machine already exists - just click on it to open the "machine drawer"
    await page.getByRole('cell', { name: 'my-dummy-machine' }).click();
  }

  // Creating the new machine opens the "machine drawer"

  // Check for "machine type" settings
  await page.getByText('Scope the printer to a specific location').waitFor();

  // Check for "machine driver" settings
  await page.getByText('Custom string for connecting').waitFor();

  // Edit the available setting
  await page.getByRole('button', { name: 'edit-setting-CONNECTION' }).click();

  const setting_value = await page
    .getByRole('textbox', { name: 'text-field-value' })
    .inputValue();

  await page
    .getByRole('textbox', { name: 'text-field-value' })
    .fill(`${setting_value}-2`);
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Setting CONNECTION updated successfully').waitFor();

  // Close the drawer
  await page.getByRole('banner').getByRole('button').first().click();
  const cell = await page.getByRole('cell', { name: 'my-dummy-machine' });

  // Let's restart the machine now
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Edit' }).waitFor();
  await page.getByRole('menuitem', { name: 'Restart' }).click();
  await page.getByText('Machine restarted').waitFor();

  // Let's print something with the machine
  await navigate(page, 'stock/location/1/stock-items');

  await page.getByRole('checkbox', { name: 'Select all records' }).click();
  await page
    .getByRole('tabpanel', { name: 'Stock Items' })
    .getByLabel('action-menu-printing-actions')
    .click();
  await page
    .getByRole('menuitem', {
      name: 'action-menu-printing-actions-print-labels'
    })
    .click();

  await page.getByLabel('related-field-plugin').fill('machine');
  await page.getByText('InvenTreeLabelMachine').click();

  await page
    .getByRole('textbox', { name: 'choice-field-machine' })
    .fill('dummy');
  await page.getByRole('option', { name: 'my-dummy-machine' }).click();

  await page
    .getByRole('button', { name: 'Print', exact: true })
    .first()
    .click();
  await page.getByText('Process completed successfully').waitFor();

  await navigate(page, 'settings/admin/machine/');

  // Finally, delete the machine configuration
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Delete' }).click();
  await page.getByRole('button', { name: 'Delete' }).click();
  await page.getByText('Machine successfully deleted.').waitFor();
});
