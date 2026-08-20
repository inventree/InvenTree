import type { HostList } from '@lib/types/Server';
import { t } from '@lingui/core/macro';

export const defaultHostList: HostList = window.INVENTREE_SETTINGS.server_list;
export const defaultHostKey = window.INVENTREE_SETTINGS.default_server;

export function translateHostName(name: string | undefined): string {
  switch (name) {
    case 'Localhost':
      return t`Local Server`;
    case 'InvenTree Demo':
      return t`InvenTree Demo`;
    case 'Current Server':
      return t`Current Server`;
    default:
      return name ?? '';
  }
}
