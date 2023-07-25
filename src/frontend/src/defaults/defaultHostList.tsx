import { t } from '@lingui/macro';

import { HostList } from '../states/states';

export const defaultHostList: HostList =
  Object.keys(window.INVENTREE_SETTINGS.server_list).length > 0
    ? window.INVENTREE_SETTINGS.server_list
    : {
        'mantine-cqj63coxn': {
          host: `${window.location.origin}/api/`,
          name: t`Current Server`
        },
        'mantine-u56l5jt85': {
          host: 'https://demo.inventree.org/api/',
          name: t`InvenTree Demo`
        }
      };
export const defaultHostKey =
  window.INVENTREE_SETTINGS.default_server || 'mantine-cqj63coxn';
