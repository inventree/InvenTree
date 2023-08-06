import { Trans } from '@lingui/macro';

import { DocumentationLinkItem } from '../components/items/DocumentationLinks';

export const footerLinks = [
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
export const navTabs = [
  { text: <Trans>Home</Trans>, name: 'home' },
  { text: <Trans>Dashboard</Trans>, name: 'dashboard' },
  { text: <Trans>Playground</Trans>, name: 'playground' },
  { text: <Trans>Parts</Trans>, name: 'parts' },
  { text: <Trans>Stock</Trans>, name: 'stock' },
  { text: <Trans>Build</Trans>, name: 'build' }
];

export const docLinks = {
  app: 'https://docs.inventree.org/en/latest/app/app/',
  getting_started: 'https://docs.inventree.org/en/latest/getting_started/',
  api: 'https://docs.inventree.org/en/latest/api/api/',
  developer: 'https://docs.inventree.org/en/latest/develop/starting/',
  faq: 'https://docs.inventree.org/en/latest/faq/'
};

export const navDocLinks: DocumentationLinkItem[] = [
  {
    id: 'getting_started',
    title: <Trans>Getting Started</Trans>,
    description: <Trans>Getting started with InvenTree</Trans>,
    link: docLinks.getting_started,
    placeholder: true
  },
  {
    id: 'api',
    title: <Trans>API</Trans>,
    description: <Trans>InvenTree API documentation</Trans>,
    link: docLinks.api
  },
  {
    id: 'developer',
    title: <Trans>Developer Manual</Trans>,
    description: <Trans>InvenTree developer manual</Trans>,
    link: docLinks.developer
  },
  {
    id: 'faq',
    title: <Trans>FAQ</Trans>,
    description: <Trans>Frequently asked questions</Trans>,
    link: docLinks.faq
  }
];

// TODO @matmair: Add the following pages and adjust the links
export const aboutLinks: DocumentationLinkItem[] = [
  {
    id: 'instance',
    title: <Trans>Instance</Trans>,
    description: <Trans>About this Inventree instance</Trans>,
    link: '/instance',
    placeholder: true
  },
  {
    id: 'about',
    title: <Trans>InvenTree</Trans>,
    description: <Trans>About the InvenTree org</Trans>,
    link: '/about',
    placeholder: true
  },
  {
    id: 'licenses',
    title: <Trans>Licenses</Trans>,
    description: <Trans>Licenses for packages used by InvenTree</Trans>,
    link: '/licenses',
    placeholder: true
  }
];
