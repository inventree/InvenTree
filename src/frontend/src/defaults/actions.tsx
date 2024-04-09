import { t } from '@lingui/macro';
import type { SpotlightAction } from '@mantine/spotlight';
import { IconFileText, IconHome, IconInfoCircle } from '@tabler/icons-react';
import { NavigateFunction } from 'react-router-dom';

import { menuItems } from './menuItems';

export function getActions(navigate: NavigateFunction) {
  /**
   * Default actions for the spotlight
   */
  const actions: SpotlightAction[] = [
    {
      title: t`Home`,
      description: `Go to the home page`,
      onTrigger: (action) => navigate(menuItems.home.link),
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
      onTrigger: () => console.log('Documentation'),
      icon: <IconFileText size="1.2rem" />
    },
    {
      title: t`About InvenTree`,
      description: t`About the InvenTree org`,
      onTrigger: () => navigate(menuItems.about.link),
      icon: <IconInfoCircle size="1.2rem" />
    }
  ];

  return actions;
}
