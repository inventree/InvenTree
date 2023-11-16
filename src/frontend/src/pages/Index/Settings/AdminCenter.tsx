import { Trans, t } from '@lingui/macro';
import {
  Anchor,
  Divider,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { useMemo } from 'react';
import { Link } from 'react-router-dom';

import { PlaceholderPill } from '../../../components/items/Placeholder';
import { PanelGroup, PanelType } from '../../../components/nav/PanelGroup';
import { SettingsHeader } from '../../../components/nav/SettingsHeader';
import { GlobalSettingList } from '../../../components/settings/SettingList';
import { GroupTable } from '../../../components/tables/settings/GroupTable';
import { UserTable } from '../../../components/tables/settings/UserTable';

/**
 * System settings page
 */
export default function AdminCenter() {
  const adminCenterPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'user',
        label: t`User Management`,
        content: (
          <Stack spacing="xs">
            <Title order={5}>
              <Trans>Users</Trans>
            </Title>
            <UserTable />
            <Title order={5}>
              <Trans>Groups</Trans>
            </Title>
            <GroupTable />
            <Divider />
            <Stack spacing={0}>
              <Text>
                <Trans>Settings</Trans>
              </Text>
              <Group>
                <Text c="dimmed">
                  <Trans>
                    Select settings relevant for user lifecycle. More available
                    in
                  </Trans>
                </Text>
                <Anchor component={Link} to={'/settings/system'}>
                  <Trans>System settings</Trans>
                </Anchor>
              </Group>
            </Stack>
            <GlobalSettingList
              keys={[
                'LOGIN_ENABLE_REG',
                'SIGNUP_GROUP',
                'LOGIN_ENABLE_SSO_REG'
              ]}
            />
          </Stack>
        )
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
    <>
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
          collabsible={false}
        />
      </Stack>
    </>
  );
}
