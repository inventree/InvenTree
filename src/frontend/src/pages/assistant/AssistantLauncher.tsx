import { ActionIcon, Indicator, Tooltip } from '@mantine/core';
import { IconMessageCircle } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useLocation, useNavigate } from 'react-router-dom';
import { useApi } from '../../contexts/ApiContext';
import { useUserState } from '../../states/UserState';
import {
  ASSISTANT_API,
  type BusinessReference,
  type HistoryPage
} from './assistant-api';

export function pageReference(path: string): BusinessReference | undefined {
  const routes: [RegExp, string, string][] = [
    [/\/part\/(\d+)(?:\/|$)/, 'part', '物料'],
    [/\/stock\/item\/(\d+)(?:\/|$)/, 'stock', '库存'],
    [/\/stock\/location\/(\d+)(?:\/|$)/, 'location', '库位'],
    [/\/purchasing\/purchase-order\/(\d+)(?:\/|$)/, 'purchase_order', '采购单'],
    [/\/manufacturing\/build-order\/(\d+)(?:\/|$)/, 'build', '工单'],
    [/\/sales\/sales-order\/(\d+)(?:\/|$)/, 'sales_order', '销售订单'],
    [/\/sales\/shipment\/(\d+)(?:\/|$)/, 'shipment', '发运单']
  ];
  for (const [pattern, object_type, label] of routes) {
    const match = path.match(pattern);
    if (match)
      return {
        object_type,
        object_id: match[1],
        label: `${label} #${match[1]}`,
        page_url: path
      };
  }
  return undefined;
}
export default function AssistantLauncher() {
  const location = useLocation();
  const navigate = useNavigate();
  const api = useApi();
  const userId = useUserState((state) => state.user?.pk);
  const onAssistant = location.pathname.includes('/assistant');
  const history = useQuery({
    queryKey: ['assistant-unread', userId],
    enabled: !onAssistant,
    queryFn: async () =>
      (
        await api.get<HistoryPage>(`${ASSISTANT_API}messages/`, {
          params: { limit: 1 }
        })
      ).data,
    refetchInterval: 30000,
    retry: false
  });
  const latest = history.data?.items.at(-1);
  const read = sessionStorage.getItem(`cangxu-assistant-read:${userId}`);
  const unread = latest?.role === 'assistant' && read !== String(latest.id);
  if (onAssistant) return null;
  return (
    <Tooltip label='工作伙伴' position='left'>
      <Indicator
        disabled={!unread}
        color='red'
        size={10}
        style={{
          position: 'fixed',
          right: 'max(20px, env(safe-area-inset-right))',
          bottom: 'max(28px, env(safe-area-inset-bottom))',
          zIndex: 190
        }}
      >
        <ActionIcon
          size={46}
          radius='xl'
          variant='filled'
          aria-label={unread ? '打开工作伙伴，有新消息' : '打开工作伙伴'}
          onClick={() =>
            navigate('/assistant/', {
              state: {
                returnTo: location.pathname + location.search,
                references: [pageReference(location.pathname)].filter(Boolean)
              }
            })
          }
        >
          <IconMessageCircle size={24} />
        </ActionIcon>
      </Indicator>
    </Tooltip>
  );
}
