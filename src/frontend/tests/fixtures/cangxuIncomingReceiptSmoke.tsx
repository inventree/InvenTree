import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import { i18n } from '@lingui/core';
import { I18nProvider } from '@lingui/react';
import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { QueryClient } from '@tanstack/react-query';
import type { AxiosInstance } from 'axios';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';

import { ApiProvider } from '../../src/contexts/ApiContext';
import { messages } from '../../src/locales/zh_Hans/messages';

i18n.load('zh_Hans', messages);
i18n.activate('zh_Hans');
const IncomingReceiptPanel = (
  await import('../../src/pages/cangxu/IncomingReceiptPanel')
).default;

const receipt = {
  id: 31,
  purchase_order_line: 7,
  purchase_order_number: 'CX-SYNTHETIC-PO-001',
  part_name: '合成 GPU 交换板',
  part_code: 'CX-DEMO-SWITCH-001',
  quantity: '1.00000',
  status: 10,
  batch_code: 'CX-DEMO-LOT-001',
  serial_numbers: ['SYNTHETIC-SERIAL-001'],
  stock_items: [51],
  inspection_id: null,
  received_at: '2026-10-12T00:00:00Z'
};

let inspection: Record<string, any> | null = null;
const calls: { method: string; url: string; payload?: unknown }[] = [];
Object.assign(window, { __incomingReceiptSmokeCalls: calls });

const api = {
  get: async (url: string) => {
    if (url.includes('purchase-receipts'))
      return { data: { results: [receipt] } };
    if (url.includes('receipt-inspections')) {
      return { data: { results: inspection ? [inspection] : [] } };
    }
    return { data: { results: [] } };
  },
  post: async (url: string, payload: Record<string, any>) => {
    calls.push({ method: 'POST', url, payload });
    if (url.includes('receipt-inspections') && url.includes('/sign/')) {
      inspection = {
        ...inspection,
        ...(payload.role === 'warehouse'
          ? { warehouse_signer: 1 }
          : { purchaser_signer: 1 })
      };
      return { data: inspection };
    }
    if (url.includes('receipt-inspections') && url.includes('/submit/')) {
      inspection = { ...inspection, state: 'pass' };
      return { data: inspection };
    }
    if (url.includes('receipt-inspections')) {
      inspection = {
        id: 41,
        ...payload,
        state: 'draft',
        warehouse_signer: null,
        purchaser_signer: null
      };
      return { data: inspection };
    }
    return { data: {} };
  }
} as unknown as AxiosInstance;

const client = new QueryClient({
  defaultOptions: { queries: { retry: false } }
});

createRoot(document.getElementById('root')!).render(
  <I18nProvider i18n={i18n}>
    <MantineProvider>
      <Notifications />
      <ApiProvider api={api} client={client}>
        <MemoryRouter>
          <IncomingReceiptPanel />
        </MemoryRouter>
      </ApiProvider>
    </MantineProvider>
  </I18nProvider>
);
