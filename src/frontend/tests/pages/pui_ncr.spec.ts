import { createApi } from '../api.js';
import { expect, generateUUID, test } from '../baseFixtures.js';
import { adminuser } from '../defaults.js';
import { clickOnRowMenu, loadTab, navigate } from '../helpers.js';
import { doCachedLogin } from '../login.js';
import { setSettingState } from '../settings.js';

// Note: The 'admin' user is used here, as the demo dataset does not
// assign the 'ncr' role to any of the other test user groups

test('NCR - Visibility', async ({ browser }) => {
  // With NCR disabled, the panel should not be available
  await setSettingState({ setting: 'NCR_ENABLED', value: false });

  const page = await doCachedLogin(browser, {
    user: adminuser,
    url: 'manufacturing/index/'
  });

  await page.getByRole('tab', { name: 'Build Orders' }).waitFor();
  await page.getByRole('tab', { name: 'Non-Conformances' }).waitFor({
    state: 'hidden'
  });

  // Enable NCR, and reload the page
  await setSettingState({ setting: 'NCR_ENABLED', value: true });

  await navigate(page, 'manufacturing/index/');
  await page.reload();

  await page.getByRole('tab', { name: 'Manufacturing' }).waitFor();
  await loadTab(page, 'Non-Conformances');
  await page
    .getByRole('button', { name: 'action-button-report-non-conformance' })
    .waitFor();
});

test('NCR - Workflow', async ({ browser }) => {
  await setSettingState({ setting: 'NCR_ENABLED', value: true });

  const page = await doCachedLogin(browser, {
    user: adminuser,
    url: 'manufacturing/index/ncr'
  });

  // Raise a new NCR
  await page
    .getByRole('button', { name: 'action-button-report-non-conformance' })
    .click();

  await page.getByLabel('related-field-part').fill('Blue Chair');
  await page
    .getByRole('option', { name: /Blue Chair/ })
    .first()
    .click();

  await page
    .getByLabel('text-field-description', { exact: true })
    .fill('Paint defect found during inspection');

  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Item Created').waitFor();

  // We should now be on the NCR detail page
  await page.waitForURL('**/manufacturing/ncr/**');
  await page.getByText('Pending').first().waitFor();

  // Link a stock item
  await loadTab(page, 'Stock Items');
  await page
    .getByRole('button', { name: 'action-button-link-stock-item' })
    .click();
  await page.getByLabel('related-field-stock_item').click();
  await page.getByRole('option').first().click();
  await page.getByRole('button', { name: 'Submit' }).click();

  // Try to complete the NCR - should fail, disposition is still pending
  await page.getByRole('button', { name: 'Complete' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page
    .getByText('All linked stock items must be assigned a disposition')
    .waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Investigate the NCR
  await page.getByRole('button', { name: 'Investigate' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('NCR is now under investigation').waitFor();
  await page.getByText('In Progress').first().waitFor();

  // Assign a disposition to the linked stock item
  const cell = page.getByRole('cell', { name: 'Pending' });
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await page.getByLabel('choice-field-disposition').click();
  await page.getByRole('option', { name: 'Scrap' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByRole('cell', { name: 'Scrap' }).waitFor();

  // Now the NCR can be completed
  await page.getByRole('button', { name: 'Complete' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('NCR completed').waitFor();
  await page.getByText('Complete').first().waitFor();

  // Transition actions are no longer available
  await page
    .getByRole('button', { name: 'Investigate' })
    .waitFor({ state: 'hidden' });

  // Check the other panels load
  await loadTab(page, 'Attachments');
  await loadTab(page, 'Notes');
});

test('NCR - Linked Panels', async ({ browser }) => {
  await setSettingState({ setting: 'NCR_ENABLED', value: true });

  const api = await createApi({});

  // Find a stock item which was received against a purchase order
  const orders = await (
    await api.get('order/po/', { params: { limit: 25 } })
  ).json();

  let item: any = undefined;

  for (const order of orders.results) {
    const items = await (
      await api.get('stock/', {
        params: { purchase_order: order.pk, limit: 1 }
      })
    ).json();

    if (items.results.length > 0) {
      item = items.results[0];
      break;
    }
  }

  expect(item).toBeDefined();

  // Raise an NCR against the item (via the API)
  const description = `Linked NCR ${generateUUID()}`;

  const response = await api.post('build/non-conformance/', {
    data: {
      part: item.part,
      purchase_order: item.purchase_order,
      description: description
    }
  });

  expect(response.status()).toBe(201);
  const ncr = await response.json();

  const link = await api.post('build/non-conformance/stock-item/', {
    data: { ncr: ncr.pk, stock_item: item.pk }
  });

  expect(link.status()).toBe(201);

  // The NCR is displayed on each linked record
  const page = await doCachedLogin(browser, { user: adminuser });

  for (const url of [
    `part/${item.part}/non-conformances`,
    `purchasing/purchase-order/${item.purchase_order}/non-conformances`,
    `stock/item/${item.pk}/non-conformances`
  ]) {
    await navigate(page, url);
    await page
      .getByRole('cell', { name: ncr.reference, exact: true })
      .waitFor();
    await page.getByRole('cell', { name: description }).waitFor();
  }
});
