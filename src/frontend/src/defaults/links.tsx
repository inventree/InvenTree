import { Trans, t } from '@lingui/macro';
import { openContextModal } from '@mantine/modals';

import { MenuLinkItem } from '../components/items/MenuLinks';
import { StylishText } from '../components/items/StylishText';
import { UserRoles } from '../enums/Roles';
import { IS_DEV_OR_DEMO } from '../main';

export const navTabs = [
  { text: <Trans>Dashboard</Trans>, name: 'home' },
  { text: <Trans>Parts</Trans>, name: 'part', role: UserRoles.part },
  { text: <Trans>Stock</Trans>, name: 'stock', role: UserRoles.stock },
  { text: <Trans>Build</Trans>, name: 'build', role: UserRoles.build },
  {
    text: <Trans>Purchasing</Trans>,
    name: 'purchasing',
    role: UserRoles.purchase_order
  },
  { text: <Trans>Sales</Trans>, name: 'sales', role: UserRoles.sales_order }
];

if (IS_DEV_OR_DEMO) {
  navTabs.push({ text: <Trans>Playground</Trans>, name: 'playground' });
}

export const docLinks = {
  app: 'https://docs.inventree.org/app/',
  getting_started: 'https://docs.inventree.org/en/latest/start/intro/',
  api: 'https://docs.inventree.org/en/latest/api/api/',
  developer: 'https://docs.inventree.org/en/latest/develop/contributing/',
  faq: 'https://docs.inventree.org/en/latest/faq/'
};

export function DocumentationLinks(): MenuLinkItem[] {
  return [
    {
      id: 'gettin-started',
      title: t`Getting Started`,
      link: docLinks.getting_started,
      external: true,
      description: t`Getting started with InvenTree`
    },
    {
      id: 'api',
      title: t`API`,
      link: docLinks.api,
      external: true,
      description: t`InvenTree API documentation`
    },
    {
      id: 'developer',
      title: t`Developer Manual`,
      link: docLinks.developer,
      external: true,
      description: t`InvenTree developer manual`
    },
    {
      id: 'faq',
      title: t`FAQ`,
      link: docLinks.faq,
      external: true,
      description: t`Frequently asked questions`
    }
  ];
}

export function serverInfo() {
  return openContextModal({
    modal: 'info',
    title: (
      <StylishText size="xl">
        <Trans>System Information</Trans>
      </StylishText>
    ),
    size: 'xl',
    innerProps: {}
  });
}

export function aboutInvenTree() {
  return openContextModal({
    modal: 'about',
    title: (
      <StylishText size="xl">
        <Trans>About InvenTree</Trans>
      </StylishText>
    ),
    size: 'xl',
    innerProps: {}
  });
}

export function licenseInfo() {
  return openContextModal({
    modal: 'license',
    title: (
      <StylishText size="xl">
        <Trans>License Information</Trans>
      </StylishText>
    ),
    size: 'xl',
    innerProps: {}
  });
}

export function AboutLinks(): MenuLinkItem[] {
  return [
    {
      id: 'instance',
      title: t`System Information`,
      description: t`About this Inventree instance`,
      icon: 'info',
      action: serverInfo
    },
    {
      id: 'about',
      title: t`About InvenTree`,
      description: t`About the InvenTree Project`,
      icon: 'info',
      action: aboutInvenTree
    },
    {
      id: 'licenses',
      title: t`License Information`,
      description: t`Licenses for dependencies of the InvenTree software`,
      icon: 'license',
      action: licenseInfo
    }
  ];
}
