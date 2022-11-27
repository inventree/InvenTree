import { HostList } from './contex/states';
import { Trans } from '@lingui/macro'


export const defaultHostList: HostList = {
  'https://demo_inventree_org': {
    host: 'https://demo.inventree.org/api/',
    name: <Trans>InvenTree Demo</Trans>
  },
  'https://sample_app_invenhost_com': {
    host: 'https://sample.app.invenhost.com/api/',
    name: <Trans>InvenHost: Sample</Trans>
  },
  'http://localhost:8000': {
    host: 'http://localhost:8000/api/',
    name: <Trans>Localhost</Trans>
  }
};

export const tabs = [
  { text: <Trans>Home</Trans>, name: 'home' },
  { text: <Trans>Part</Trans>, name: 'part' }
];

export const links = [
  {
    link: 'https://inventree.org/',
    label: <Trans>Website</Trans>
  },
  {
    link: 'https://github.com/invenhost/InvenTree',
    label: <Trans>GitHub</Trans>
  },
  {
    link: 'https://demo.inventree.org/',
    label: <Trans>Demo</Trans>
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
