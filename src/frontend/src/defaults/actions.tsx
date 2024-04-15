import { t } from '@lingui/macro';
import type { SpotlightActionData } from '@mantine/spotlight';
import { IconHome, IconLink, IconPointer } from '@tabler/icons-react';
import { NavigateFunction } from 'react-router-dom';

import { useLocalState } from '../states/LocalState';
import { aboutInvenTree, docLinks, licenseInfo, serverInfo } from './links';
import { menuItems } from './menuItems';

export function getActions(navigate: NavigateFunction) {
  const setNavigationOpen = useLocalState((state) => state.setNavigationOpen);

  const actions: SpotlightActionData[] = [
    {
      id: 'home',
      title: t`Home`,
      description: `Go to the home page`,
      onClick: () => navigate(menuItems.home.link),
      leftSection: <IconHome size="1.2rem" />
    },
    {
      id: 'dashboard',
      title: t`Dashboard`,
      description: t`Go to the InvenTree dashboard`,
      onClick: () => navigate(menuItems.dashboard.link),
      leftSection: <IconLink size="1.2rem" />
    },
    {
      id: 'documentation',
      title: t`Documentation`,
      description: t`Visit the documentation to learn more about InvenTree`,
      onClick: () => (window.location.href = docLinks.faq),
      leftSection: <IconLink size="1.2rem" />
    },
    {
      id: 'about',
      title: t`About InvenTree`,
      description: t`About the InvenTree org`,
      onClick: () => aboutInvenTree(),
      leftSection: <IconLink size="1.2rem" />
    },
    {
      id: 'server-info',
      title: t`Server Information`,
      description: t`About this Inventree instance`,
      onClick: () => serverInfo(),
      leftSection: <IconLink size="1.2rem" />
    },
    {
      id: 'license-info',
      title: t`License Information`,
      description: t`Licenses for dependencies of the service`,
      onClick: () => licenseInfo(),
      leftSection: <IconLink size="1.2rem" />
    },
    {
      id: 'navigation',
      title: t`Open Navigation`,
      description: t`Open the main navigation menu`,
      onClick: () => setNavigationOpen(true),
      leftSection: <IconPointer size="1.2rem" />
    }
  ];

  return actions;
}
