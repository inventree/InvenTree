import { createApi } from '../api.js';
import { expect, generateUUID, test } from '../baseFixtures.js';
import { openDetailAction } from '../helpers.js';
import { doCachedLogin } from '../login.js';
import { setSettingState } from '../settings.js';

/**
 * Tests that the part settings are respected by the part forms.
 * Each test restores the (default) setting values when complete.
 */

/**
 * Create a new part via the API, returning the created part data
 */
const createPart = async (data: object) => {
  const api = await createApi({});
  const response = await api.post('part/', {
    data: {
      name: `Settings part ${generateUUID().slice(0, 8)}`,
      description: 'Part for settings tests',
      ...data
    }
  });
  expect(response.status(), await response.text()).toBe(201);
  const part = await response.json();
  await api.dispose();
  return part;
};

/**
 * Remove a part created by createPart()
 */
const deletePartById = async (pk: number) => {
  const api = await createApi({});
  await api.patch(`part/${pk}/`, { data: { active: false } });
  await api.delete(`part/${pk}/`);
  await api.dispose();
};

test('Parts - Settings - Create Part Form', async ({ browser }) => {
  const openCreateForm = async (page) => {
    await page.getByRole('button', { name: 'action-menu-add-parts' }).click();
    await page
      .getByRole('menuitem', { name: 'action-menu-add-parts-create-part' })
      .click();
    await page.getByLabel('text-field-name', { exact: true }).waitFor();
  };

  const copyParameters = (page) =>
    page.getByRole('switch', {
      name: 'boolean-field-copy_category_parameters'
    });

  const supplierField = (page) =>
    page.getByLabel('related-field-initial_supplier.supplier');

  try {
    await setSettingState({
      setting: 'PART_CATEGORY_PARAMETERS',
      value: false
    });
    await setSettingState({ setting: 'PART_CREATE_SUPPLIER', value: false });
    await setSettingState({ setting: 'PART_ALLOW_EDIT_IPN', value: false });

    const page = await doCachedLogin(browser, {
      url: 'part/category/index/parts'
    });

    // Disabled: parameters are not copied by default, and supplier data is not offered
    await openCreateForm(page);
    await expect(copyParameters(page)).not.toBeChecked();
    await expect(supplierField(page)).toHaveCount(0);

    // The IPN can always be set when creating a new part
    await expect(
      page.getByRole('textbox', { name: 'text-field-IPN' })
    ).toBeEnabled();
    await page.getByRole('button', { name: 'Cancel' }).click();

    await setSettingState({ setting: 'PART_CATEGORY_PARAMETERS', value: true });
    await setSettingState({ setting: 'PART_CREATE_SUPPLIER', value: true });

    // Enabled: parameters are copied by default, and supplier data is offered
    await page.reload();
    await openCreateForm(page);
    await expect(copyParameters(page)).toBeChecked();
    await expect(supplierField(page)).toBeVisible();
    await page.getByRole('button', { name: 'Cancel' }).click();
  } finally {
    await setSettingState({ setting: 'PART_CATEGORY_PARAMETERS', value: true });
    await setSettingState({ setting: 'PART_CREATE_SUPPLIER', value: true });
    await setSettingState({ setting: 'PART_ALLOW_EDIT_IPN', value: true });
  }
});

test('Parts - Settings - Duplicate Part Tests', async ({ browser }) => {
  const part = await createPart({ testable: true });

  const copyTests = (page) =>
    page.getByRole('switch', { name: 'boolean-field-duplicate.copy_tests' });

  try {
    await setSettingState({ setting: 'PART_COPY_TESTS', value: false });

    const page = await doCachedLogin(browser, {
      url: `part/${part.pk}/details`
    });

    // Disabled: test templates are not copied by default
    await openDetailAction(page, 'part', 'duplicate');
    await expect(copyTests(page)).not.toBeChecked();
    await page.getByRole('button', { name: 'Cancel' }).click();

    await setSettingState({ setting: 'PART_COPY_TESTS', value: true });

    // Enabled: test templates are copied by default
    await page.reload();
    await openDetailAction(page, 'part', 'duplicate');
    await expect(copyTests(page)).toBeChecked();
    await page.getByRole('button', { name: 'Cancel' }).click();
  } finally {
    await setSettingState({ setting: 'PART_COPY_TESTS', value: true });
    await deletePartById(part.pk);
  }
});

test('Parts - Settings - Edit IPN', async ({ browser }) => {
  const part = await createPart({ IPN: `IPN-${generateUUID().slice(0, 8)}` });

  const ipnField = (page) =>
    page.getByRole('textbox', { name: 'text-field-IPN' });

  try {
    await setSettingState({ setting: 'PART_ALLOW_EDIT_IPN', value: false });

    const page = await doCachedLogin(browser, {
      url: `part/${part.pk}/details`
    });

    // Disabled: the IPN of an existing part cannot be edited
    await openDetailAction(page, 'part', 'edit');
    await expect(ipnField(page)).toHaveValue(part.IPN);
    await expect(ipnField(page)).toBeDisabled();
    await page.getByRole('button', { name: 'Cancel' }).click();

    await setSettingState({ setting: 'PART_ALLOW_EDIT_IPN', value: true });

    // Enabled: the IPN can be edited
    await page.reload();
    await openDetailAction(page, 'part', 'edit');
    await expect(ipnField(page)).toBeEnabled();
    await page.getByRole('button', { name: 'Cancel' }).click();
  } finally {
    await setSettingState({ setting: 'PART_ALLOW_EDIT_IPN', value: true });
    await deletePartById(part.pk);
  }
});
