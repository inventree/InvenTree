import { Trans, t } from '@lingui/macro';
import { Divider, Paper, SimpleGrid, Stack, Text, Title } from '@mantine/core';
import {
  IconListDetails,
  IconPlugConnected,
  IconUsersGroup
} from '@tabler/icons-react';
import { lazy, useMemo } from 'react';

import { PlaceholderPill } from '../../../../components/items/Placeholder';
import { PanelGroup, PanelType } from '../../../../components/nav/PanelGroup';
import { SettingsHeader } from '../../../../components/nav/SettingsHeader';
import { GlobalSettingList } from '../../../../components/settings/SettingList';
import { Loadable } from '../../../../functions/loading';

const UserManagementPanel = Loadable(
  lazy(() => import('./UserManagementPanel'))
);

const PluginManagementPanel = Loadable(
  lazy(() => import('./PluginManagementPanel'))
);

const ProjectCodeTable = Loadable(
  lazy(() => import('../../../../components/tables/settings/ProjectCodeTable'))
);

export default function AdminCenter() {
  const adminCenterPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'user',
        label: t`Users`,
        icon: <IconUsersGroup />,
        content: <UserManagementPanel />
      },
      {
        name: 'projectcodes',
        label: t`Project Codes`,
        icon: <IconListDetails />,
        content: (
          <Stack spacing="xs">
            <GlobalSettingList keys={['PROJECT_CODES_ENABLED']} />
            <Divider />
            <ProjectCodeTable />
          </Stack>
        )
      },
      {
        name: 'plugin',
        label: t`Plugins`,
        icon: <IconPlugConnected />,
        content: <PluginManagementPanel />
      }
    ];
  }, []);

  const QuickAction = () => (
    <Stack spacing={'xs'} ml={'sm'}>
      <Title order={5}>
        <Trans>Quick Actions</Trans>
      </Title>
      <SimpleGrid cols={3}>
        <Paper shadow="xs" p="sm" withBorder>
          <Text>
            <Trans>Add a new user</Trans>
          </Text>
        </Paper>

        <Paper shadow="xs" p="sm" withBorder>
          <PlaceholderPill />
        </Paper>

        <Paper shadow="xs" p="sm" withBorder>
          <PlaceholderPill />
        </Paper>
      </SimpleGrid>
    </Stack>
  );

  return (
    <Stack spacing="xs">
      <SettingsHeader
        title={t`Admin Center`}
        subtitle={t`Advanced Options`}
        switch_link="/settings/system"
        switch_text="System Settings"
      />
      <QuickAction />
      <PanelGroup
        pageKey="admin-center"
        panels={adminCenterPanels}
        collapsible={false}
      />
    </Stack>
  );
}
