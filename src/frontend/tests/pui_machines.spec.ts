import test from 'playwright/test';
import { clickOnRowMenu } from './helpers';
import { doCachedLogin } from './login';

test('Machines - Activation', async ({ browser, request }) => {
  const page = await doCachedLogin(browser, {
    username: 'admin',
    password: 'inventree',
    url: 'settings/admin/machine'
  });

  await page.getByRole('button', { name: 'action-button-add-machine' }).click();
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

  // Creating the new machine opens the "machine drawer"

  // Check for "machine type" settings
  await page.getByText('Scope the printer to a specific location').waitFor();

  // Check for "machine driver" settings
  await page.getByText('Custom string for connecting').waitFor();

  // Edit the available setting
  await page.getByRole('button', { name: 'edit-setting-CONNECTION' }).click();
  await page
    .getByRole('textbox', { name: 'text-field-value' })
    .fill('a new value');
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

  // Finally, delete the machine configuration
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Delete' }).click();
  await page.getByRole('button', { name: 'Delete' }).click();
  await page.getByText('Machine successfully deleted.').waitFor();
});
