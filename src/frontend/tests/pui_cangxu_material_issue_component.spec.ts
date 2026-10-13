import { expect, test } from '@playwright/test';

test('Chinese material issue and partial return flow', async ({ page }) => {
  await page.goto(
    'http://localhost:5173/tests/fixtures/cangxu-material-issue-smoke.html'
  );
  await expect(page.getByText('耗材领退料')).toBeVisible();

  await page.getByRole('combobox', { name: '生产工单' }).click();
  await page.getByRole('option', { name: /CX-BUILD-SYN-001/ }).click();
  await page.getByRole('combobox', { name: '耗材BOM行' }).click();
  await page.getByRole('option', { name: /CX-DEMO-CABLE-001/ }).click();
  await page
    .getByRole('combobox', { name: '可用库存' })
    .fill('CX-DEMO-LOT-001');
  await page.getByRole('option', { name: /CX-DEMO-CABLE-001/ }).click();
  await page.getByLabel('领料数量').fill('3');
  await page.getByRole('button', { name: '确认领料' }).click();
  await expect(page.getByText('领料已记录')).toBeVisible();

  await page.getByRole('tab', { name: '退回未用物料' }).click();
  await page.getByRole('combobox', { name: '原发料记录' }).click();
  await page
    .getByRole('option', { name: /CX-BUILD-SYN-001.*GPU 供电线束/ })
    .click();
  await page.getByLabel('退料数量').fill('1');
  await page.getByRole('combobox', { name: '退回库位' }).click();
  await page.getByRole('option', { name: '合成生产库' }).click();
  await page.getByRole('button', { name: '确认退料' }).click();
  await expect(page.getByText('物料已退回', { exact: true })).toBeVisible();

  const calls = await page.evaluate(
    () => (window as any).__materialIssueSmokeCalls
  );
  expect(calls).toHaveLength(2);
  expect(calls[0].url).toContain('material-issues');
  expect(calls[0].payload).toMatchObject({
    build_line: 17,
    stock_item: 42,
    quantity: '3'
  });
  expect(calls[1].url).toContain('return_stock');
  expect(calls[1].payload).toMatchObject({ quantity: '1', location: 9 });
});
