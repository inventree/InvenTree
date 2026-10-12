import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import { i18n } from '@lingui/core';
import { I18nProvider } from '@lingui/react';
import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { QueryClient } from '@tanstack/react-query';
import type { AxiosInstance } from 'axios';
import { createRoot } from 'react-dom/client';
import { ApiProvider } from '../../src/contexts/ApiContext';
import { messages } from '../../src/locales/zh_Hans/messages';
import ShipmentReceiptPanel from '../../src/pages/sales/ShipmentReceiptPanel';
i18n.load('zh_Hans', messages);
i18n.activate('zh_Hans');
const manifest = {
  id: 3,
  package_code: 'SYN-BOX-01',
  checked_at: '2026-10-12T00:00:00Z',
  signed_at: null
};
const lines = [
  {
    id: 8,
    manifest: 3,
    stock_item: 17,
    quantity: '2.00000',
    item_role: 'GPU',
    stock_item_detail: {
      serial: 'SYNTHETIC-SERIAL-001',
      part_detail: { name: '合成 GPU 加速卡', IPN: 'CX-DEMO-GPU-001' }
    }
  }
];
let openExceptions: unknown[] = [];
const calls: { method: string; url: string; payload?: unknown }[] = [];
Object.assign(window, { __receiptSmokeCalls: calls });
const api = {
  get: async (url: string) => {
    if (url.includes('shipment-manifests')) return { data: [manifest] };
    if (url.includes('manifest-lines')) return { data: lines };
    if (url.includes('receipt-exceptions')) return { data: openExceptions };
    return { data: [] };
  },
  post: async (url: string, payload: unknown) => {
    calls.push({ method: 'POST', url, payload });
    if (url.includes('shipment-receipts')) {
      openExceptions = [
        {
          id: 91,
          kind: 'damaged',
          expected_quantity: '2.00000',
          received_quantity: '1.00000',
          notes: '外箱受损'
        }
      ];
      return { data: { id: 51 } };
    }
    if (url.includes('resolve')) {
      openExceptions = [];
      return { data: { id: 91, state: 'resolved' } };
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
        <ShipmentReceiptPanel shipmentId={4} shipped />
      </ApiProvider>
    </MantineProvider>
  </I18nProvider>
);
