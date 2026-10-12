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
import MaterialIssuePanel from '../../src/pages/cangxu/MaterialIssuePanel';

i18n.load('zh_Hans', messages);
i18n.activate('zh_Hans');

const build = {
  pk: 7,
  reference: 'CX-BUILD-SYN-001',
  title: 'Synthetic GPU server build',
  part_detail: { name: '合成 GPU 服务器', IPN: 'CX-DEMO-SERVER-001' },
  status: 10,
  status_text: 'Pending',
  quantity: '1.00000',
  completed: '0.00000'
};
const line = {
  pk: 17,
  build: 7,
  consumable: true,
  trackable: false,
  quantity: '5.00000',
  consumed: '0.00000',
  part_detail: { name: 'GPU 供电线束', IPN: 'CX-DEMO-CABLE-001' }
};
const location = {
  pk: 9,
  name: '合成生产库',
  external: false,
  structural: false
};
const stock = {
  pk: 42,
  part_detail: { name: 'GPU 供电线束', IPN: 'CX-DEMO-CABLE-001' },
  quantity: '8.00000',
  location: 9,
  location_detail: { name: location.name },
  status: 10,
  in_stock: true,
  allocated: false
};
let issue: Record<string, unknown> | null = null;
const calls: { method: string; url: string; payload?: unknown }[] = [];
Object.assign(window, { __materialIssueSmokeCalls: calls });

const api = {
  get: async (url: string) => {
    if (url.includes('build/line/')) return { data: { results: [line] } };
    if (url.includes('build/')) return { data: { results: [build] } };
    if (url.includes('stock/location/')) {
      return { data: { results: [location] } };
    }
    if (url.includes('stock/')) return { data: { results: [stock] } };
    if (url.includes('material-issues/')) {
      return { data: { results: issue ? [issue] : [] } };
    }
    return { data: { results: [] } };
  },
  post: async (url: string, payload: Record<string, unknown>) => {
    calls.push({ method: 'POST', url, payload });
    if (url.includes('return_stock')) {
      issue = {
        ...issue,
        returned_quantity: '1.00000',
        remaining_quantity: '2.00000'
      };
      return { data: issue };
    }
    issue = {
      id: 31,
      build_line: 17,
      build_reference: build.reference,
      part_name: 'GPU 供电线束',
      part_code: 'CX-DEMO-CABLE-001',
      stock_item: 42,
      quantity: String(payload.quantity),
      returned_quantity: '0.00000',
      remaining_quantity: String(payload.quantity)
    };
    return { data: issue };
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
        <MaterialIssuePanel />
      </ApiProvider>
    </MantineProvider>
  </I18nProvider>
);
