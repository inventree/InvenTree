import { HostList } from './context/states';
import { MantineSize } from '@mantine/core';
import { Trans } from '@lingui/macro'


export const defaultHostList: HostList = {
  'mantine-u56l5jt85': {
    host: 'https://demo.inventree.org/api/',
    name: 'InvenTree Demo'
  },
  'mantine-g8t1zrj50': {
    host: 'https://sample.app.invenhost.com/api/',
    name: 'InvenHost: Sample'
  },
  'mantine-cqj63coxn': {
    host: 'http://localhost:8000/api/',
    name: 'Localhost'
  }
};

export const tabs = [
  { text: <Trans>Home</Trans>, name: 'home' },
  { text: <Trans>Part</Trans>, name: 'part' }
];

export const links = [
  {
    link: 'https://inventree.org/',
    label: <Trans>Website</Trans>,
    key: 'website'
  },
  {
    link: 'https://github.com/invenhost/InvenTree',
    label: <Trans>GitHub</Trans>,
    key: 'github'
  },
  {
    link: 'https://demo.inventree.org/',
    label: <Trans>Demo</Trans>,
    key: 'demo'
  }
];

export const defaultUser = {
  name: 'Matthias Mair',
  email: 'code@mjmair.com',
  username: 'mjmair'
};

export const emptyServerAPI = {
  server: null,
  version: null,
  instance: null,
  apiVersion: null,
  worker_running: null,
  worker_pending_tasks: null,
  plugins_enabled: null,
  active_plugins: []
};

export interface SiteMarkProps {
  value: number
  label: MantineSize
}

export const SizeMarks: SiteMarkProps[] = [
  { value: 0, label: 'xs' },
  { value: 25, label: 'sm' },
  { value: 50, label: 'md' },
  { value: 75, label: 'lg' },
  { value: 100, label: 'xl' },
];
