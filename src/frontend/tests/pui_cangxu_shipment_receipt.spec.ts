import { expect, test } from '@playwright/test';

test('Chinese shipment receipt and discrepancy resolution flow', async ({
  page
}) => {
  await page.goto(
    'http://localhost:5173/tests/fixtures/cangxu-receipt-smoke.html'
  );
  await expect(page.getByText('客户签收')).toBeVisible();
  await page.getByRole('combobox', { name: '已核验包装' }).click();
  await page.getByRole('option', { name: 'SYN-BOX-01' }).click();
  await expect(page.getByText('合成 GPU 加速卡')).toBeVisible();
  await page.getByLabel('物料 17 的实收数量').fill('1');
  await page.getByRole('combobox', { name: '物料 17 的收货状态' }).click();
  await page.getByRole('option', { name: '到货损坏' }).click();
  await page.getByLabel('物料 17 的差异说明').fill('外箱受损');
  await page.getByLabel('签收人').fill('演示收货人');
  await page.getByRole('button', { name: '完成签收' }).click();
  await expect(page.getByText('签收已完成')).toBeVisible();
  await expect(page.getByText('待处理交付差异')).toBeVisible();
  await expect(page.getByText('外箱受损')).toBeVisible();
  await page.getByLabel('处理结果').fill('已安排补发，原件隔离待返修。');
  await page.getByRole('button', { name: '关闭差异' }).click();
  await expect(page.getByText('交付差异已关闭')).toBeVisible();
  await expect(page.getByText('待处理交付差异')).toHaveCount(0);
  const calls = await page.evaluate(() => (window as any).__receiptSmokeCalls);
  expect(calls).toHaveLength(2);
  expect(calls[0].url).toContain('shipment-receipts');
  expect(calls[0].payload).toMatchObject({
    recipient_name: '演示收货人',
    is_final: true,
    lines: [{ quantity_received: '1', condition: 'damaged', notes: '外箱受损' }]
  });
  expect(calls[1].url).toContain('resolve');
  expect(calls[1].payload).toMatchObject({
    resolution: '已安排补发，原件隔离待返修。'
  });
});
