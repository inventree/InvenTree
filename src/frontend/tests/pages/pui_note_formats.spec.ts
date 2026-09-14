import { expect } from '@playwright/test';
import { test } from '../baseFixtures';
import { adminuser } from '../defaults';
import { loadTab } from '../helpers';
import { doCachedLogin } from '../login';

for (const format of ['JSON', 'Plain text']) {
  test(`Notes - ${format} source editing`, async ({ browser }) => {
    const page = await doCachedLogin(browser, { url: 'part/71/details' });
    await loadTab(page, 'Notes');
    await page.getByRole('button', { name: 'Add Note', exact: true }).click();
    await page
      .getByLabel('text-field-title', { exact: true })
      .fill(`Raw ${format}`);
    await page.getByLabel('choice-field-content_type').click();
    await page.getByRole('option', { name: format, exact: true }).click();
    await page.getByRole('button', { name: 'Submit', exact: true }).click();

    const content =
      format === 'JSON'
        ? ' \n{"number":9007199254740993,"html":"<script>alert(1)</script>","escaped":"\\u010d"}\n'
        : '\n# A heading\n\n<script>alert(1)</script>\n';
    await page.getByRole('button', { name: 'edit-note', exact: true }).click();
    const editor = page.getByRole('textbox', {
      name: 'Note content',
      exact: true
    });
    await editor.fill(content);
    const saved = page.waitForResponse(
      (response) =>
        response.url().includes('/api/note/') &&
        response.request().method() === 'PATCH'
    );
    await page.getByRole('button', { name: 'save-note', exact: true }).click();
    expect((await (await saved).json()).content).toBe(content);
    await expect(editor).toHaveValue(content);

    await editor.fill(format === 'JSON' ? '{"changed":true}' : '# Changed');
    await page.getByRole('button', { name: 'reset-note', exact: true }).click();
    await expect(editor).toHaveValue(content);

    if (format === 'JSON') {
      await editor.fill('{');
      await page
        .getByRole('button', { name: 'save-note', exact: true })
        .click();
      await expect(
        page
          .getByRole('alert', { name: 'Error', exact: true })
          .filter({ hasText: 'Invalid JSON' })
      ).toBeVisible();
      await expect(editor).toHaveValue('{');
      await page
        .getByRole('button', { name: 'reset-note', exact: true })
        .click();
    }

    await page
      .getByRole('button', { name: 'finish-editing-note', exact: true })
      .click();
    await expect(page.getByTestId('raw-note-content')).toHaveText(content, {
      useInnerText: false
    });
    expect(await page.getByTestId('raw-note-content').textContent()).toBe(
      content
    );
    await expect(
      page.getByTestId('raw-note-content').locator('script')
    ).toHaveCount(0);
    await page.close();
  });
}

for (const template of [false, true]) {
  test(`Notes - permanent content type${template ? ' template' : ''}`, async ({
    browser
  }) => {
    const page = await doCachedLogin(browser, {
      url: template ? 'settings/admin/notes/' : 'part/71/details',
      user: template ? adminuser : undefined
    });
    if (!template) await loadTab(page, 'Notes');
    await page.getByRole('button', { name: 'Add Note', exact: true }).click();
    await page
      .getByLabel('text-field-title', { exact: true })
      .fill(`Permanent format ${template}`);
    await page.getByLabel('choice-field-content_type').click();
    await page.getByRole('option', { name: 'JSON', exact: true }).click();
    const created = page.waitForResponse(
      (r) => r.url().includes('/api/note/') && r.request().method() === 'POST'
    );
    await page.getByRole('button', { name: 'Submit', exact: true }).click();
    expect(await (await created).json()).toMatchObject({
      content_type: 'application/json',
      content: '{}'
    });

    await page
      .getByRole('button', { name: 'action-menu-note-actions', exact: true })
      .click();
    await expect(
      page.getByRole('menuitem').filter({ hasText: 'Change format' })
    ).toHaveCount(0);
    await page
      .getByRole('menuitem', {
        name: 'action-menu-note-actions-edit',
        exact: true
      })
      .click();
    const dialog = page.getByRole('dialog');
    await expect(dialog.getByLabel('choice-field-content_type')).toHaveCount(0);
    await dialog
      .getByLabel('text-field-title', { exact: true })
      .fill(`Renamed permanent format ${template}`);
    const updated = page.waitForResponse(
      (r) => r.url().includes('/api/note/') && r.request().method() === 'PATCH'
    );
    await dialog.getByRole('button', { name: 'Submit', exact: true }).click();
    expect(await (await updated).json()).toMatchObject({
      content_type: 'application/json',
      content: '{}'
    });
    await expect(page.getByTestId('raw-note-content')).toHaveText('{}');
    await page.close();
  });
}
