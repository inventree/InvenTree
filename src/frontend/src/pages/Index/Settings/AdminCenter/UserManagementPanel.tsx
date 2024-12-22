import { Trans } from '@lingui/macro';
import { Anchor, Divider, Group, Stack, Text, Title } from '@mantine/core';
import { Link } from 'react-router-dom';

import { GlobalSettingList } from '../../../../components/settings/SettingList';
import { GroupTable } from '../../../../tables/settings/GroupTable';
import { UserTable } from '../../../../tables/settings/UserTable';

export default function UserManagementPanel() {
  return (
    <Stack gap='xs'>
      <Title order={5}>
        <Trans>Users</Trans>
      </Title>
      <UserTable />

      <Divider />

      <Title order={5}>
        <Trans>Groups</Trans>
      </Title>
      <GroupTable />

      <Divider />

      <Stack gap={0}>
        <Text>
          <Trans>Settings</Trans>
        </Text>
        <Group>
          <Text c='dimmed'>
            <Trans>
              Select settings relevant for user lifecycle. More available in
            </Trans>
          </Text>
          <Anchor component={Link} to={'/settings/system'}>
            <Trans>System Settings</Trans>
          </Anchor>
        </Group>
      </Stack>
      <GlobalSettingList
        keys={['LOGIN_ENABLE_REG', 'SIGNUP_GROUP', 'LOGIN_ENABLE_SSO_REG']}
      />
    </Stack>
  );
}
