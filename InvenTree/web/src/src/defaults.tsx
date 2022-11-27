import { HostList } from './contex/states';
import { t } from '@lingui/macro'


export const defaultHostList: HostList = {
  'https://demo_inventree_org': {
    host: 'https://demo.inventree.org/api/',
    name: t`InvenTree Demo`
  },
  'https://sample_app_invenhost_com': {
    host: 'https://sample.app.invenhost.com/api/',
    name: t`InvenHost: Sample`
  },
  'http://localhost:8000': {
    host: 'http://localhost:8000/api/',
    name: t`Localhost`
  }
};

export const tabs = [
  { text: t`Home`, name: 'home' },
  { text: t`Part`, name: 'part' }
];

export const links = [
  {
    link: 'https://inventree.org/',
    label: t`Website`
  },
  {
    link: 'https://github.com/invenhost/InvenTree',
    label: t`GitHub`
  },
  {
    link: 'https://demo.inventree.org/',
    label: t`Demo`
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
