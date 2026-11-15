/**
 * Tests for detail page tables:
 * - Attachment upload (drag and drop zone) / edit / delete
 * - BOM table optional columns
 * - Transfer order line item actions
 */

import { createApi } from '../api.js';
import { expect, generateUUID, test } from '../baseFixtures.js';
import { clickOnRowMenu, loadTab } from '../helpers.js';
import { doCachedLogin } from '../login.js';

test('Attachments - Upload, Edit and Delete', async ({ browser }) => {
  const filename = `pw-upload-${generateUUID().slice(0, 8)}.txt`;

  const page = await doCachedLogin(browser, { url: 'part/69/attachments' });

  await page.getByText('Drag attachment file here to upload').waitFor();

  // Upload a file via the dropzone
  await page
    .locator('input[type="file"]')
    .first()
    .setInputFiles({
      name: filename,
      mimeType: 'text/plain',
      buffer: Buffer.from('Playwright attachment upload test')
    });

  await page.getByText(`File ${filename} uploaded successfully`).waitFor();

  const cell = page.getByRole('cell', { name: filename });
  await cell.waitFor();

  // Edit the attachment
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await page
    .getByLabel('text-field-comment', { exact: true })
    .fill('Uploaded by playwright');
  await page.waitForTimeout(300);
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByRole('cell', { name: 'Uploaded by playwright' }).waitFor();

  // Delete the attachment
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Delete' }).click();
  await page
    .getByRole('dialog', { name: 'Delete Attachment' })
    .getByRole('button', { name: 'Delete' })
    .click();
  await expect(page.getByRole('cell', { name: filename })).toHaveCount(0);
});

test('BOM - Optional Columns', async ({ browser }) => {
  // "Widget Assembly Variant" - BOM items with setup quantity
  const page = await doCachedLogin(browser, { url: 'part/81/bom' });
  await page.waitForLoadState('networkidle');

  const columns = [
    'Setup Quantity',
    'Attrition',
    'Rounding Multiple',
    'Piece Count',
    'Substitutes'
  ];

  // Enable the optional columns
  await page.getByLabel('table-select-columns').click();
  for (const column of columns) {
    await page.getByRole('menuitem', { name: column, exact: true }).click();
  }
  await page.keyboard.press('Escape');
  await page.waitForLoadState('networkidle');

  // Check that the columns are displayed
  for (const column of columns) {
    await page.locator('table thead th', { hasText: column }).first().waitFor();
  }

  // Disable them again
  await page.getByLabel('table-select-columns').click();
  for (const column of columns) {
    await page.getByRole('menuitem', { name: column, exact: true }).click();
  }
  await page.keyboard.press('Escape');
});

test('Transfer Orders - Line Item Actions', async ({ browser }) => {
  const api = await createApi({});
  const reference = `TO-${Math.floor(10000 + Math.random() * 89999)}`;

  const response = await api.post('order/transfer-order/', {
    data: {
      reference: reference,
      description: 'Playwright line item actions',
      take_from: 7,
      destination: 12
    }
  });
  expect(response.status()).toBe(201);
  const order = await response.json();

  // Lines: purchaseable part, assembly part, trackable part
  for (const part of [85, 108, 87]) {
    const line = await api.post('order/transfer-order-line/', {
      data: { order: order.pk, part: part, quantity: 2 }
    });
    expect(line.status()).toBe(201);
  }

  const page = await doCachedLogin(browser, {
    url: `stock/transfer-order/${order.pk}/line-items`
  });

  await loadTab(page, 'Line Items');

  const rows = page
    .getByRole('tabpanel', { name: 'Line Items' })
    .locator('table tbody tr');

  const rowMenu = async (index: number, action: string) => {
    await rows
      .nth(index)
      .getByLabel(/row-action-menu-/i)
      .click();
    await page.getByRole('menuitem', { name: action }).click();
  };

  await rows.nth(2).waitFor();

  // Try the "extra" row actions available on each line
  for (let idx = 0; idx < 3; idx++) {
    await rows
      .nth(idx)
      .getByLabel(/row-action-menu-/i)
      .click();

    const menu = page.getByRole('menu');
    await menu.waitFor();
    await page.waitForTimeout(250);

    const actions = await menu.getByRole('menuitem').allInnerTexts();
    const names = actions.map((a) => a.trim());

    if (names.includes('Order stock')) {
      await menu.getByRole('menuitem', { name: 'Order stock' }).click();
      const wizard = page.getByRole('dialog', { name: 'Order Parts' });
      await wizard.waitFor();
      await wizard.getByRole('banner').getByRole('button').click();
      await expect(wizard).toHaveCount(0);
    } else if (names.includes('Allocate serials')) {
      await menu.getByRole('menuitem', { name: 'Allocate serials' }).click();
      await page.getByRole('button', { name: 'Cancel' }).click();
    } else if (names.includes('Build stock')) {
      await menu.getByRole('menuitem', { name: 'Build stock' }).click();
      await page.getByRole('button', { name: 'Cancel' }).click();
    } else {
      // Close the menu by clicking the toggle again
      await rows
        .nth(idx)
        .getByLabel(/row-action-menu-/i)
        .click();
    }

    await expect(page.getByRole('menu')).toHaveCount(0);
  }

  // The "build stock" action for the assembly line
  for (let idx = 0; idx < 3; idx++) {
    await rows
      .nth(idx)
      .getByLabel(/row-action-menu-/i)
      .click();
    const menu = page.getByRole('menu');
    await menu.waitFor();
    await page.waitForTimeout(250);
    const build = menu.getByRole('menuitem', { name: 'Build stock' });

    if ((await build.count()) > 0) {
      await build.click();
      await page.getByRole('button', { name: 'Cancel' }).click();
      break;
    }

    await rows
      .nth(idx)
      .getByLabel(/row-action-menu-/i)
      .click();
    await expect(page.getByRole('menu')).toHaveCount(0);
  }

  // Edit, duplicate and delete the first line
  await rowMenu(0, 'Edit');
  await page.getByRole('button', { name: 'Cancel' }).click();
  await rowMenu(0, 'Duplicate');
  await page.getByRole('button', { name: 'Cancel' }).click();
  await rowMenu(0, 'Delete');
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Delete', exact: true })
    .click();
  await page.waitForLoadState('networkidle');

  // Cleanup - cancel the order
  await api.post(`order/transfer-order/${order.pk}/cancel/`, {});
});
