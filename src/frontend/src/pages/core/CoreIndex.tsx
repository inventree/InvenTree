import { Trans, t } from '@lingui/macro';
import { Stack, Text } from '@mantine/core';
import { IconOutlet, IconUser, IconUsersGroup } from '@tabler/icons-react';
import { useMemo } from 'react';

import PermissionDenied from '../../components/errors/PermissionDenied';
import { PlaceholderPill } from '../../components/items/Placeholder';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/panels/PanelGroup';
import { useUserState } from '../../states/UserState';
import { UserTable } from '../../tables/core/UserTable';
import { GroupTable } from '../../tables/settings/GroupTable';

const Overiew = () => {
  return (
    <Stack>
      <Text>
        <Trans>
          Discover users, groups and contacts in this instance via the left
          panel
        </Trans>
      </Text>
      <PlaceholderPill />
    </Stack>
  );
};

export default function CoreIndex() {
  const user = useUserState();

  const panels = useMemo(() => {
    return [
      {
        name: 'index',
        label: t`Overview`,
        icon: <IconOutlet />,
        content: <Overiew />
      },
      {
        name: 'users',
        label: t`Users`,
        icon: <IconUser />,
        content: <UserTable />
      },
      {
        name: 'groups',
        label: t`Groups`,
        icon: <IconUsersGroup />,
        content: <GroupTable directLink />
      }
    ];
  }, []);

  if (!user.isLoggedIn()) {
    return <PermissionDenied />;
  }

  return (
    <Stack>
      <PageDetail title={t`System Overview`} />
      <PanelGroup pageKey='core-index' panels={panels} id={null} />
    </Stack>
  );
}
