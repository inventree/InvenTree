import { HostList } from './contex/states';

export const defaultHostList: HostList = {
  'https://demo.inventree.org': {
    host: 'https://demo.inventree.org/api/',
    name: 'InvenTree Demo'
  },
  'https://sample.app.invenhost.com': {
    host: 'https://sample.app.invenhost.com/api/',
    name: 'InvenHost: Sample'
  },
  'http://localhost:8000': {
    host: 'http://localhost:8000/api/',
    name: 'Localhost'
  }
};

export const tabs = [
  { text: 'Home', name: 'home' },
  { text: 'Part', name: 'part' }
];

export const links = {
  links: [
    {
      link: 'https://inventree.org/',
      label: 'Website'
    },
    {
      link: 'https://github.com/invenhost/InvenTree',
      label: 'GitHub'
    },
    {
      link: 'https://demo.inventree.org/',
      label: 'Demo'
    }
  ]
};

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
