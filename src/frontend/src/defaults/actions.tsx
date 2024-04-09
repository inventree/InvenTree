import { t } from '@lingui/macro';
import type { SpotlightAction } from '@mantine/spotlight';
import {
  IconFileText,
  IconHome,
  IconInfoCircle,
  IconNavigation
} from '@tabler/icons-react';
import { NavigateFunction } from 'react-router-dom';

import { useLocalState } from '../states/LocalState';
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
      icon: <IconHome size="1.2rem" />
    },
    {
      title: t`Documentation`,
      description: t`Visit documentation to learn more about InvenTree`,
      onTrigger: () => log('Documentatioconsole.n'),
      icon: <IconFileText size="1.2rem" />
    },
    {
      title: t`About InvenTree`,
      description: t`About the InvenTree org`,
      onTrigger: () => navigate(menuItems.about.link),
      icon: <IconInfoCircle size="1.2rem" />
    },
    {
      title: t`Open Navigation`,
      description: t`Open the main navigation menu`,
      onTrigger: () => setNavigationOpen(true),
      icon: <IconNavigation size="1.2rem" />
    }
  ];

  return actions;
}
