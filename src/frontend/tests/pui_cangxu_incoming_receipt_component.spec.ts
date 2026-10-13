import { expect, test } from '@playwright/test';

test('Chinese incoming receipt inspection and archive flow', async ({
  page
}) => {
  page.setDefaultTimeout(5000);
  await page.goto(
    'http://localhost:5173/tests/fixtures/cangxu-incoming-receipt-smoke.html'
  );
  await expect(
    page.getByLabel('按采购单号、物料名称或物料编码搜索')
  ).toBeVisible();
  await expect(page.getByText('CX-SYNTHETIC-PO-001')).toBeVisible();
  await expect(page.getByText('合成 GPU 交换板')).toBeVisible();
  await page.getByRole('button', { name: '检验与归档' }).click();

  await page.getByRole('combobox', { name: '检验方式' }).click();
  await page.getByRole('option', { name: '全检' }).click();
  await page.getByLabel('抽检数量').fill('1');
  await page.getByRole('combobox', { name: '型号' }).click();
  await page.getByRole('option', { name: '相符' }).click();
  await page.getByRole('combobox', { name: '数量' }).click();
  await page.getByRole('option', { name: '相符' }).click();
  await page.getByRole('combobox', { name: '包装' }).click();
  await page.getByRole('option', { name: '完好' }).click();
  await page.getByRole('button', { name: '保存验收记录' }).click();

  await page.getByRole('button', { name: '仓管签字' }).click();
  await page.getByRole('button', { name: '采购签字' }).click();
  await page.getByRole('button', { name: '提交验收' }).click();
  await expect(page.getByText('pass', { exact: true })).toBeVisible();

  const calls = await page.evaluate(
    () => (window as any).__incomingReceiptSmokeCalls
  );
  expect(calls).toHaveLength(4);
  expect(calls[0].url).toContain('receipt-inspections');
  expect(calls[0].payload).toMatchObject({
    receipt: 31,
    sampling_method: 'full',
    sampled_quantity: 1,
    model_result: 'match',
    quantity_result: 'match',
    packaging_condition: 'intact'
  });
  expect(calls.slice(1, 3).map((call: any) => call.payload.role)).toEqual([
    'warehouse',
    'purchaser'
  ]);
  expect(calls[3].url).toContain('/submit/');
});
