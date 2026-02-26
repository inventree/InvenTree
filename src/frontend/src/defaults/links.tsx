import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { openContextModal } from '@mantine/modals';

import { UserRoles } from '@lib/enums/Roles';
import type { SettingsStateProps } from '@lib/types/Settings';
import type { UserStateProps } from '@lib/types/User';
import {
  IconBox,
  IconBuildingFactory2,
  IconDashboard,
  IconPackages,
  IconShoppingCart,
  IconTruckDelivery
} from '@tabler/icons-react';
import type { ReactNode } from 'react';
import type { MenuLinkItem } from '../components/items/MenuLinks';
import { StylishText } from '../components/items/StylishText';

type NavTab = {
  name: string;
  title: string;
  icon: ReactNode;
  role?: UserRoles;
};

export function getNavTabs(user: UserStateProps): NavTab[] {
  const navTabs: NavTab[] = [
    {
      name: 'home',
      title: t`Dashboard`,
      icon: <IconDashboard />
    },
    {
      name: 'part',
      title: t`Parts`,
      icon: <IconBox />,
      role: UserRoles.part
    },
    {
      name: 'stock',
      title: t`Stock`,
      icon: <IconPackages />,
      role: UserRoles.stock
    },
    {
      name: 'manufacturing',
      title: t`Manufacturing`,
      icon: <IconBuildingFactory2 />,
      role: UserRoles.build
    },
    {
      name: 'purchasing',
      title: t`Purchasing`,
      icon: <IconShoppingCart />,
      role: UserRoles.purchase_order
    },
    {
      name: 'sales',
      title: t`Sales`,
      icon: <IconTruckDelivery />,
      role: UserRoles.sales_order
    }
  ];

  return navTabs.filter((tab) => {
    if (!tab.role) return true;
    return user.hasViewRole(tab.role);
  });
}

export const docLinks = {
  app: 'https://docs.inventree.org/en/latest/app/',
  getting_started: 'https://docs.inventree.org/en/latest/start/',
  api: 'https://docs.inventree.org/en/latest/api/',
  developer: 'https://docs.inventree.org/en/latest/develop/contributing/',
  faq: 'https://docs.inventree.org/en/latest/faq/',
  github: 'https://github.com/inventree/inventree',
  errorcodes: 'https://docs.inventree.org/en/latest/sref/error-codes/'
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
    },
    {
      id: 'github',
      title: t`GitHub Repository`,
      link: docLinks.github,
      external: true,
      description: t`InvenTree source code on GitHub`
    }
  ];
}

export function serverInfo() {
  return openContextModal({
    modal: 'info',
    title: (
      <StylishText size='xl'>
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
      <StylishText size='xl'>
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
      <StylishText size='xl'>
        <Trans>License Information</Trans>
      </StylishText>
    ),
    size: 'xl',
    innerProps: {}
  });
}

export function AboutLinks(
  settings: SettingsStateProps,
  user: UserStateProps
): MenuLinkItem[] {
  const base_items: MenuLinkItem[] = [
    {
      id: 'instance',
      title: t`System Information`,
      description: t`About this InvenTree instance`,
      icon: 'info',
      action: serverInfo
    },
    {
      id: 'licenses',
      title: t`License Information`,
      description: t`Licenses for dependencies of the InvenTree software`,
      icon: 'license',
      action: licenseInfo
    }
  ];

  // Restrict the about link if that setting is set
  if (user.isSuperuser() || !settings.isSet('INVENTREE_RESTRICT_ABOUT')) {
    base_items.push({
      id: 'about',
      title: t`About InvenTree`,
      description: t`About the InvenTree Project`,
      icon: 'info',
      action: aboutInvenTree
    });
  }
  return base_items;
}
