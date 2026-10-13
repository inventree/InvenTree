import { expect, test } from '@playwright/test';

const entry =
  'http://localhost:5173/tests/fixtures/cangxu-assistant-smoke.html';
const image = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aIuoAAAAASUVORK5CYII=',
  'base64'
);
const attachment = {
  id: '55555555-5555-4555-8555-555555555555',
  name: '虚构验收照片.png',
  mime_type: 'image/png',
  size: image.length,
  download_url:
    '/api/cangxu/assistant/attachments/55555555-5555-4555-8555-555555555555/download/',
  preview_url:
    '/api/cangxu/assistant/attachments/55555555-5555-4555-8555-555555555555/preview/'
};

// The deployed LAN HTTP origin does not expose the secure-context UUID API.
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(globalThis.crypto, 'randomUUID', {
      value: undefined,
      configurable: true
    });
  });
});

test('assistant-ui image preview, reference and stable retry through HTTP', async ({
  page
}) => {
  const requests: any[] = [];
  let items: any[] = [];
  const pageErrors: string[] = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  await page.route('**/api/cangxu/assistant/**', async (route) => {
    const request = route.request();
    const url = request.url();
    if (url.includes('/status/'))
      return route.fulfill({
        json: { reply_running: false, is_running: false, status: 'available' }
      });
    if (url.includes('/preview/') || url.includes('/download/'))
      return route.fulfill({ contentType: 'image/png', body: image });
    if (url.includes('/attachments/') && request.method() === 'POST')
      return route.fulfill({ json: attachment });
    if (request.method() === 'POST') {
      const body = request.postDataJSON();
      requests.push(body);
      if (requests.length === 1) return route.abort('failed');
      items = [
        {
          id: 1,
          role: 'user',
          text: body.text,
          request_id: body.client_request_id,
          attachments: [attachment],
          references: body.references
        },
        {
          id: 2,
          role: 'assistant',
          text: '已查询虚构记录。\n\n| 物料 | 数量 |\n| --- | --- |\n| 虚构组件 | 1 |\n\n```json\n{"checked":true}\n```'
        }
      ];
      return route.fulfill({ status: 201, json: { status: 'pending' } });
    }
    return route.fulfill({
      json: { items, next_before: null, has_more: false, pending: [] }
    });
  });
  await page.goto(entry);
  await expect(page.getByRole('textbox', { name: '消息内容' })).toBeVisible();
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: '添加图片或附件' }).click();
  await (await chooser).setFiles({
    name: attachment.name,
    mimeType: 'image/png',
    buffer: image
  });
  await expect(page.locator('.partner-file')).toHaveCount(1);
  await page.getByRole('button', { name: `预览 ${attachment.name}` }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.keyboard.press('Escape');
  await page
    .getByRole('textbox', { name: '消息内容' })
    .fill('请检查这份虚构资料');
  await page.getByRole('button', { name: '发送消息' }).click();
  await page.getByRole('button', { name: '重试本次发送' }).click();
  await expect(page.getByText('已查询虚构记录。')).toBeVisible();
  expect(requests).toHaveLength(2);
  expect(requests[1]).toMatchObject({
    client_request_id: requests[0].client_request_id,
    attachments: [attachment.id],
    references: [{ object_type: 'part', object_id: '12' }],
    retry: true
  });
  await expect(page.getByRole('table')).toBeVisible();
  await expect(page.getByRole('button', { name: '复制代码' })).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth
    )
  ).toBeTruthy();
  expect(pageErrors).toEqual([]);
});

test('draft, removable reference, dark mobile and real stop control', async ({
  page
}) => {
  const controls: any[] = [];
  await page.route('**/api/cangxu/assistant/**', async (route) => {
    if (route.request().url().includes('/status/'))
      return route.fulfill({
        json: {
          reply_running: controls.length === 0,
          is_running: controls.length === 0,
          status: 'processing',
          live_message: {
            id: 'live:1',
            role: 'assistant',
            text: '正在核对虚构资料'
          }
        }
      });
    if (route.request().method() === 'POST') {
      controls.push(route.request().postDataJSON());
      return route.fulfill({ status: 201, json: { acknowledged: true } });
    }
    return route.fulfill({
      json: { items: [], next_before: null, has_more: false, pending: [] }
    });
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`${entry}?theme=dark`);
  await expect(page.getByText('正在核对虚构资料')).toBeVisible();
  await page.getByRole('textbox', { name: '消息内容' }).fill('保留的虚构草稿');
  await page.getByRole('button', { name: '移除引用 虚构物料 #12' }).click();
  await expect(page.getByText('虚构物料 #12')).toHaveCount(0);
  await page.getByRole('button', { name: '停止回复' }).click();
  expect(controls[0]).toMatchObject({ scope: 'reply' });
  await page.reload();
  await expect(page.getByRole('textbox', { name: '消息内容' })).toHaveValue(
    '保留的虚构草稿'
  );
  await expect(page.getByText('虚构物料 #12')).toHaveCount(0);
  expect(
    await page.evaluate(() =>
      document.documentElement.getAttribute('data-mantine-color-scheme')
    )
  ).toBe('dark');
});

test('paste and drag images use the same upload pipeline and draft removal', async ({
  page
}) => {
  let uploads = 0;
  let removals = 0;
  await page.route('**/api/cangxu/assistant/**', async (route) => {
    if (route.request().method() === 'POST') {
      uploads++;
      return route.fulfill({ json: attachment });
    }
    if (route.request().method() === 'DELETE') {
      removals++;
      return route.fulfill({ status: 204 });
    }
    if (route.request().url().includes('/preview/'))
      return route.fulfill({ contentType: 'image/png', body: image });
    if (route.request().url().includes('/status/'))
      return route.fulfill({
        json: { reply_running: false, is_running: false, status: 'available' }
      });
    return route.fulfill({
      json: { items: [], has_more: false, next_before: null, pending: [] }
    });
  });
  await page.goto(entry);
  const input = page.getByRole('textbox', { name: '消息内容' });
  await input.waitFor();
  await input.evaluate(
    (element, bytes) => {
      const transfer = new DataTransfer();
      transfer.items.add(
        new File([new Uint8Array(bytes)], '虚构验收照片.png', {
          type: 'image/png'
        })
      );
      element.dispatchEvent(
        new ClipboardEvent('paste', {
          clipboardData: transfer,
          bubbles: true,
          cancelable: true
        })
      );
    },
    [...image]
  );
  await expect(
    page.getByRole('button', { name: '下载 虚构验收照片.png' })
  ).toBeVisible();
  await page.getByRole('button', { name: '移除 虚构验收照片.png' }).click();
  await expect(page.locator('.partner-file')).toHaveCount(0);
  expect(removals).toBe(1);
  await page.locator('.partner-dropzone').evaluate(
    (element, bytes) => {
      const transfer = new DataTransfer();
      transfer.items.add(
        new File([new Uint8Array(bytes)], '虚构验收照片.png', {
          type: 'image/png'
        })
      );
      element.dispatchEvent(
        new DragEvent('drop', {
          dataTransfer: transfer,
          bubbles: true,
          cancelable: true
        })
      );
    },
    [...image]
  );
  await expect(
    page.getByRole('button', { name: '下载 虚构验收照片.png' })
  ).toBeVisible();
  expect(uploads).toBe(2);
});

test('uploads serialize and retry stable keys; unsent draft files restore with ownership checks', async ({
  page
}) => {
  let active = 0;
  let maximumActive = 0;
  let failed = false;
  let metadataReads = 0;
  const keys: string[] = [];
  const uploads = new Map<string, any>();
  const sent: any[] = [];
  await page.route('**/api/cangxu/assistant/**', async (route) => {
    const request = route.request();
    const url = request.url();
    if (url.includes('/status/'))
      return route.fulfill({
        json: { reply_running: true, is_running: true, status: 'processing' }
      });
    if (url.includes('/preview/'))
      return route.fulfill({ contentType: 'image/png', body: image });
    if (url.includes('/attachments/') && request.method() === 'POST') {
      active++;
      maximumActive = Math.max(maximumActive, active);
      const raw = request.postDataBuffer()!.toString();
      const key = raw.match(/name="client_upload_id"\r\n\r\n([^\r]+)/)![1];
      keys.push(key);
      await new Promise((resolve) => setTimeout(resolve, 75));
      active--;
      if (!failed) {
        failed = true;
        return route.fulfill({
          status: 503,
          json: { detail: 'synthetic transient' }
        });
      }
      const id = key;
      const file = {
        ...attachment,
        id,
        name: `虚构-${uploads.size + 1}.png`,
        preview_url: `/api/cangxu/assistant/attachments/${id}/preview/`,
        download_url: `/api/cangxu/assistant/attachments/${id}/download/`
      };
      uploads.set(id, file);
      return route.fulfill({ json: file });
    }
    if (url.includes('/attachments/')) {
      metadataReads++;
      const id = url.match(/attachments\/([^/]+)\//)![1];
      return route.fulfill({ json: uploads.get(id) });
    }
    if (request.method() === 'POST') {
      sent.push(request.postDataJSON());
      return route.fulfill({ status: 201, json: { status: 'pending' } });
    }
    return route.fulfill({
      json: { items: [], has_more: false, next_before: null, pending: [] }
    });
  });
  await page.goto(entry);
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: '添加图片或附件' }).click();
  await (await chooser).setFiles([
    { name: '一.png', mimeType: 'image/png', buffer: image },
    { name: '二.png', mimeType: 'image/png', buffer: image }
  ]);
  await expect(page.getByRole('button', { name: /^下载 / })).toHaveCount(2);
  expect(maximumActive).toBe(1);
  expect(keys).toHaveLength(3);
  expect(keys[0]).toBe(keys[1]);
  await expect
    .poll(() =>
      page.evaluate(() =>
        Object.entries(sessionStorage).some(
          ([key, value]) =>
            key.endsWith(':attachments') && JSON.parse(value).length === 2
        )
      )
    )
    .toBe(true);
  await page.reload();
  await expect(page.getByRole('button', { name: /下载 虚构-/ })).toHaveCount(2);
  expect(metadataReads).toBe(2);
  expect(sent).toHaveLength(0);
  expect(keys).toHaveLength(3);
  await page
    .getByRole('textbox', { name: '消息内容' })
    .fill('处理中的补充资料');
  await page.getByRole('button', { name: '发送消息' }).click();
  await expect.poll(() => sent.length).toBe(1);
  expect(sent[0].attachments).toHaveLength(2);
});

test('removing a queued upload keeps the remaining upload queue usable', async ({
  page
}) => {
  let active = 0;
  let maximumActive = 0;
  let uploads = 0;
  await page.route('**/api/cangxu/assistant/**', async (route) => {
    const request = route.request();
    if (request.method() === 'POST') {
      active++;
      maximumActive = Math.max(maximumActive, active);
      uploads++;
      const raw = request.postDataBuffer()!.toString();
      const id = raw.match(/name="client_upload_id"\r\n\r\n([^\r]+)/)![1];
      await new Promise((resolve) => setTimeout(resolve, 300));
      active--;
      return route.fulfill({ json: { ...attachment, id } });
    }
    if (request.method() === 'DELETE') return route.fulfill({ status: 204 });
    if (request.url().includes('/preview/'))
      return route.fulfill({ contentType: 'image/png', body: image });
    if (request.url().includes('/status/'))
      return route.fulfill({
        json: { is_running: false, reply_running: false, status: 'available' }
      });
    return route.fulfill({
      json: { items: [], has_more: false, next_before: null, pending: [] }
    });
  });
  await page.goto(entry);
  const select = async (names: string[]) => {
    const choice = page.waitForEvent('filechooser');
    await page.getByRole('button', { name: '添加图片或附件' }).click();
    await (await choice).setFiles(
      names.map((name) => ({ name, mimeType: 'image/png', buffer: image }))
    );
  };
  await select(['保留.png', '移除.png']);
  await page.getByRole('button', { name: '移除 移除.png' }).click();
  await select(['补充.png']);
  await expect(
    page.getByRole('button', { name: '下载 保留.png' })
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: '下载 补充.png' })
  ).toBeVisible();
  await expect(page.locator('.partner-file')).toHaveCount(2);
  expect(uploads).toBe(2);
  expect(maximumActive).toBe(1);
});

test('Enter on LAN HTTP immediately shows submission, then receives a reply', async ({
  page
}) => {
  const requests: any[] = [];
  const pageErrors: string[] = [];
  let items: any[] = [];
  let release!: () => void;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  page.on('pageerror', (error) => pageErrors.push(error.message));
  await page.route('**/api/cangxu/assistant/**', async (route) => {
    if (route.request().url().includes('/status/'))
      return route.fulfill({
        json: { reply_running: false, is_running: false }
      });
    if (route.request().method() === 'POST') {
      const body = route.request().postDataJSON();
      requests.push(body);
      await held;
      items = [
        {
          id: 1,
          role: 'user',
          text: body.text,
          request_id: body.client_request_id
        },
        { id: 2, role: 'assistant', text: '已查询：虚构库存记录共 555 条。' }
      ];
      return route.fulfill({ status: 201, json: { status: 'pending' } });
    }
    return route.fulfill({
      json: { items, pending: [], next_before: null, has_more: false }
    });
  });
  await page.goto(entry);
  const input = page.getByRole('textbox', { name: '消息内容' });
  await input.fill('现在有多少库存？');
  await input.press('Enter');
  await expect(input).toHaveValue('');
  await expect(
    page.getByText('现在有多少库存？', { exact: true })
  ).toBeVisible();
  await expect.poll(() => requests.length).toBe(1);
  expect(requests[0].client_request_id).toMatch(
    /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
  );
  release();
  await expect(page.getByText('已查询：虚构库存记录共 555 条。')).toBeVisible();
  expect(pageErrors).toEqual([]);
});
