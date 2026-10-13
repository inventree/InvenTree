import { expect, test } from '@playwright/test';
const entry =
  'http://localhost:5173/tests/fixtures/cangxu-assistant-workbench.html';
const names = [
  '工作伙伴',
  '库存伙伴',
  '采购伙伴',
  '生产伙伴',
  '质量伙伴',
  '维修伙伴',
  '交付伙伴'
];
const partners = names.map((name, index) => ({
  partner_id: `10000000-0000-4000-8000-${String(index + 1).padStart(12, '0')}`,
  conversation_id: `20000000-0000-4000-8000-${String(index + 1).padStart(12, '0')}`,
  display_name: name,
  is_default: index === 0,
  enabled: true,
  write_enabled: true,
  created_at: '2026-10-13T10:19:00Z',
  updated_at: '2026-10-13T10:19:00Z',
  last_message: [
    '入库资料已归档，可以继续处理下一批。',
    '已核对库存，发现 2 项需要补货。',
    '收货安排已更新，等待供应商确认。',
    '工单已经准备好，装配可以继续。',
    '检验记录已整理，异常等待处置。',
    '维修进度已更新，待回收部件。',
    '本批交付材料已齐备。'
  ][index],
  last_message_at: '2026-10-13T10:19:00Z'
}));
async function mock(page: any) {
  const state = {
    partners: partners.map((p) => ({ ...p })),
    messages: new Map<string, any[]>(),
    requests: [] as any[]
  };
  for (const partner of partners)
    state.messages.set(partner.partner_id, [
      {
        id: 1,
        role: 'assistant',
        text: partner.last_message,
        created_at: '2026-10-13T10:19:00Z'
      }
    ]);
  state.messages.set(partners[1].partner_id, [
    {
      id: 1,
      role: 'assistant',
      text: '可以。我会先查询当前库存，再核对待收货的采购单。你希望我重点关注哪些物料？',
      created_at: '2026-10-13T10:19:00Z'
    },
    {
      id: 2,
      role: 'user',
      text: '检查计算板卡、交换部件和线缆的可用库存。\n\n对照本周工单的 BOM，列出缺料和已下单未收货的部分；发现来料异常时，记录事实并按原流程处理。',
      created_at: '2026-10-13T10:20:00Z'
    }
  ]);
  await page.addInitScript(() =>
    Object.defineProperty(crypto, 'randomUUID', {
      value: undefined,
      configurable: true
    })
  );
  await page.route('**/api/cangxu/assistant/**', async (route: any) => {
    const req = route.request();
    const url = new URL(req.url());
    const id = url.searchParams.get('partner_id') || partners[0].partner_id;
    if (url.pathname.endsWith('/partners/') && req.method() === 'GET')
      return route.fulfill({ json: { results: state.partners } });
    if (url.pathname.endsWith('/partners/') && req.method() === 'POST') {
      const body = req.postDataJSON();
      const next = {
        ...partners[0],
        partner_id: '10000000-0000-4000-8000-999999999999',
        is_default: false,
        display_name: body.display_name,
        last_message: ''
      };
      state.partners.push(next);
      state.messages.set(next.partner_id, []);
      return route.fulfill({ status: 201, json: next });
    }
    if (req.method() === 'PATCH') {
      const partner = state.partners.find((p) =>
        url.pathname.includes(p.partner_id)
      )!;
      Object.assign(partner, req.postDataJSON());
      return route.fulfill({ json: partner });
    }
    if (url.pathname.endsWith('/status/'))
      return route.fulfill({
        json: { status: 'available', is_running: false, reply_running: false }
      });
    if (req.method() === 'POST') {
      const body = req.postDataJSON();
      state.requests.push({ id, body });
      const history = state.messages.get(id)!;
      history.push(
        {
          id: history.length + 1,
          role: 'user',
          text: body.text,
          request_id: body.client_request_id
        },
        {
          id: history.length + 2,
          role: 'assistant',
          text: `${state.partners.find((p) => p.partner_id === id)?.display_name}已接收：${body.text}`
        }
      );
      return route.fulfill({ status: 201, json: { status: 'acknowledged' } });
    }
    return route.fulfill({
      json: {
        items: state.messages.get(id) || [],
        pending: [],
        has_more: false,
        next_before: null
      }
    });
  });
  return state;
}
test('sidebar searches real partners, switches isolated histories and preserves drafts', async ({
  page
}) => {
  const state = await mock(page);
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(entry);
  await expect(page.locator('.partner-message-assistant')).toContainText(
    '入库资料已归档'
  );
  await page
    .getByRole('button', { name: '打开伙伴 库存伙伴', exact: true })
    .click();
  await expect(
    page.getByText(
      '可以。我会先查询当前库存，再核对待收货的采购单。你希望我重点关注哪些物料？'
    )
  ).toBeVisible();
  const input = page.getByRole('textbox', { name: '消息内容' });
  await input.fill('库存伙伴的独立草稿');
  await page
    .getByRole('button', { name: '打开伙伴 采购伙伴', exact: true })
    .click();
  await expect(input).toHaveValue('');
  await expect(
    page.getByText('收货安排已更新，等待供应商确认。').last()
  ).toBeVisible();
  await expect(
    page.getByText(
      '可以。我会先查询当前库存，再核对待收货的采购单。你希望我重点关注哪些物料？'
    )
  ).toHaveCount(0);
  await input.fill('查询虚构采购单');
  await input.press('Enter');
  await expect(
    page
      .locator('.partner-message-assistant')
      .getByText('采购伙伴已接收：查询虚构采购单')
  ).toBeVisible();
  expect(state.requests[0].id).toBe(partners[2].partner_id);
  expect(
    await page.evaluate(() =>
      sessionStorage.getItem('cangxu-assistant-read:42')
    )
  ).toBe('1');
  await page
    .getByRole('button', { name: '打开伙伴 库存伙伴', exact: true })
    .click();
  await expect(input).toHaveValue('库存伙伴的独立草稿');
  await page.getByRole('textbox', { name: '搜索伙伴' }).fill('质量');
  await expect(page.locator('.partner-list-item')).toHaveCount(1);
  await page.getByRole('textbox', { name: '搜索伙伴' }).fill('');
  await expect(page.locator('.partner-list-item')).toHaveCount(7);
  expect(errors).toEqual([]);
});
test('partner creation and rename persist through API and mobile list navigation', async ({
  page
}) => {
  const state = await mock(page);
  await page.goto(entry);
  await page.getByRole('button', { name: '新建伙伴', exact: true }).click();
  await page.getByRole('textbox', { name: '伙伴名称' }).fill('附件归档伙伴');
  await page.getByRole('button', { name: '创建伙伴', exact: true }).click();
  await expect(
    page.getByRole('button', { name: '打开伙伴 附件归档伙伴', exact: true })
  ).toHaveAttribute('aria-current', 'page');
  expect(state.partners).toHaveLength(8);
  await page.getByRole('button', { name: '更多操作', exact: true }).click();
  await page.getByRole('menuitem', { name: '重命名伙伴' }).click();
  await page.getByRole('textbox', { name: '伙伴名称' }).fill('归档伙伴');
  await page.getByRole('button', { name: '保存名称', exact: true }).click();
  await expect(
    page.getByRole('button', { name: '打开伙伴 归档伙伴', exact: true })
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole('textbox', { name: '消息内容' })).toBeVisible();
  await expect(
    page.getByRole('textbox', { name: '搜索伙伴' })
  ).not.toBeVisible();
  await page.getByRole('button', { name: '伙伴列表', exact: true }).click();
  await expect(page.getByRole('textbox', { name: '搜索伙伴' })).toBeVisible();
  await page
    .getByRole('button', { name: '打开伙伴 库存伙伴', exact: true })
    .click();
  await expect(page.getByRole('textbox', { name: '消息内容' })).toBeVisible();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)
  ).toBe(false);
});
test('reference layout renders sidebar, bubbles and fixed composer on desktop and mobile', async ({
  page
}) => {
  await mock(page);
  await page.setViewportSize({ width: 1952, height: 1273 });
  await page.goto(entry);
  await page
    .getByRole('button', { name: '打开伙伴 库存伙伴', exact: true })
    .click();
  await expect(page.locator('.partner-message-user')).toBeVisible();
  await expect(page.locator('.partner-list-item.is-selected')).toHaveCSS(
    'background-color',
    'rgb(39, 39, 39)'
  );
  await page.screenshot({
    path: '/tmp/cangxu-workbench-desktop.png',
    animations: 'disabled'
  });
  const sizes = await page.evaluate(() => {
    const shell = document
      .querySelector('.partner-workbench')!
      .getBoundingClientRect();
    const rail = document
      .querySelector('.partner-sidebar')!
      .getBoundingClientRect();
    const composer = document
      .querySelector('.partner-composer')!
      .getBoundingClientRect();
    return {
      fraction: rail.width / shell.width,
      bottom: composer.bottom,
      overflow: document.documentElement.scrollWidth > innerWidth
    };
  });
  expect(sizes.fraction).toBeGreaterThan(0.27);
  expect(sizes.fraction).toBeLessThan(0.3);
  expect(sizes.bottom).toBeLessThan(1273);
  expect(sizes.overflow).toBe(false);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: '/tmp/cangxu-workbench-mobile.png' });
  await page.getByRole('button', { name: '伙伴列表', exact: true }).click();
  await page.screenshot({ path: '/tmp/cangxu-workbench-mobile-list.png' });
});

test('copy works on plain HTTP without the secure clipboard API', async ({
  page
}) => {
  await mock(page);
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'clipboard', {
      value: undefined,
      configurable: true
    });
    document.execCommand = () => {
      (window as any).__copied = (
        document.activeElement as HTMLTextAreaElement
      ).value;
      return true;
    };
  });
  await page.goto(entry);
  await expect(page.locator('.partner-message-assistant')).toContainText(
    '入库资料已归档'
  );
  await page.locator('.partner-message-assistant').hover();
  await page.getByRole('button', { name: '复制消息', exact: true }).click();
  expect(await page.evaluate(() => (window as any).__copied)).toBe(
    partners[0].last_message
  );
});

test('failed creation keeps the name and shows an error inside the dialog', async ({
  page
}) => {
  await mock(page);
  await page.route('**/api/cangxu/assistant/partners/', async (route) => {
    if (route.request().method() === 'POST')
      return route.fulfill({
        status: 503,
        json: { detail: 'Synthetic unavailable' }
      });
    return route.fallback();
  });
  await page.goto(entry);
  await page.getByRole('button', { name: '新建伙伴', exact: true }).click();
  await page.getByRole('textbox', { name: '伙伴名称' }).fill('保留的伙伴名称');
  await page.screenshot({
    path: '/tmp/cangxu-workbench-create.png',
    animations: 'disabled'
  });
  await page.getByRole('button', { name: '创建伙伴', exact: true }).click();
  await expect(
    page
      .getByRole('dialog')
      .getByText('工作伙伴暂时无法连接；原业务页面仍可使用。')
  ).toBeVisible();
  await expect(page.getByRole('textbox', { name: '伙伴名称' })).toHaveValue(
    '保留的伙伴名称'
  );
});

test('switching partners leaves the running background reply alone', async ({
  page
}) => {
  await mock(page);
  const stops: string[] = [];
  page.on('request', (request) => {
    if (request.method() === 'POST' && request.url().includes('/controls/'))
      stops.push(request.url());
  });
  await page.route('**/api/cangxu/assistant/status/**', async (route) => {
    const running =
      new URL(route.request().url()).searchParams.get('partner_id') ===
      partners[0].partner_id;
    return route.fulfill({
      json: {
        status: running ? 'processing' : 'available',
        reply_running: running,
        is_running: running
      }
    });
  });
  await page.goto(entry);
  await expect(page.getByRole('button', { name: '停止回复' })).toBeVisible();
  await page
    .getByRole('button', { name: '打开伙伴 库存伙伴', exact: true })
    .click();
  await expect(page.getByRole('textbox', { name: '消息内容' })).toHaveAttribute(
    'placeholder',
    '发送给库存伙伴…'
  );
  await expect(page.getByRole('button', { name: '停止回复' })).toHaveCount(0);
  expect(stops).toEqual([]);
});
