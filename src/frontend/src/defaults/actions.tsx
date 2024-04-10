import { t } from '@lingui/macro';
import type { SpotlightAction } from '@mantine/spotlight';
import { IconHome, IconLink, IconPointer } from '@tabler/icons-react';
import { NavigateFunction } from 'react-router-dom';

import { useLocalState } from '../states/LocalState';
import { aboutInvenTree, docLinks, licenseInfo, serverInfo } from './links';
import { menuItems } from './menuItems';

export function getActions(navigate: NavigateFunction) {
  const setNavigationOpen = useLocalState((state) => state.setNavigationOpen);

  const actions: SpotlightAction[] = [
    {
      title: t`Home`,
      description: `Go to the home page`,
      onTrigger: () => navigate(menuItems.home.link),
      icon: <IconHome size="1.2rem" />
    },
    {
      title: t`Dashboard`,
      description: t`Go to the InvenTree dashboard`,
      onTrigger: () => navigate(menuItems.dashboard.link),
      icon: <IconLink size="1.2rem" />
    },
    {
      title: t`Documentation`,
      description: t`Visit the documentation to learn more about InvenTree`,
      onTrigger: () => (window.location.href = docLinks.faq),
      icon: <IconLink size="1.2rem" />
    },
    {
      title: t`About InvenTree`,
      description: t`About the InvenTree org`,
      onTrigger: () => aboutInvenTree(),
      icon: <IconLink size="1.2rem" />
    },
    {
      title: t`Server Information`,
      description: t`About this Inventree instance`,
      onTrigger: () => serverInfo(),
      icon: <IconLink size="1.2rem" />
    },
    {
      title: t`License Information`,
      description: t`Licenses for dependencies of the service`,
      onTrigger: () => licenseInfo(),
      icon: <IconLink size="1.2rem" />
    },
    {
      title: t`Open Navigation`,
      description: t`Open the main navigation menu`,
      onTrigger: () => setNavigationOpen(true),
      icon: <IconPointer size="1.2rem" />
    }
  ];

  return actions;
}
