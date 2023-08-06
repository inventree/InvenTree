import { t } from '@lingui/macro';

import { HostList } from '../states/states';

export const defaultHostList: HostList = {
  'mantine-u56l5jt85': {
    host: 'https://demo.inventree.org/api/',
    name: t`InvenTree Demo`
  },
  'mantine-g8t1zrj50': {
    host: 'https://sample.app.invenhost.com/api/',
    name: 'InvenHost: Sample'
  },
  'mantine-cqj63coxn': {
    host: 'http://localhost:8000/api/',
    name: t`Local Server`
  }
};
export const defaultHostKey = 'mantine-cqj63coxn';
