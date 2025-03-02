import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import { IconUser, IconUsersGroup } from '@tabler/icons-react';
import { useMemo } from 'react';

import PermissionDenied from '../../components/errors/PermissionDenied';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/panels/PanelGroup';
import { useUserState } from '../../states/UserState';
import { ContactTable } from '../../tables/company/ContactTable';
import { UserTable } from '../../tables/core/UserTable';
import { GroupTable } from '../../tables/settings/GroupTable';

export default function CoreIndex() {
  const user = useUserState();

  const panels = useMemo(() => {
    return [
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
      },
      {
        name: 'contacts',
        label: t`Contacts`,
        icon: <IconUsersGroup />,
        content: <ContactTable />
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
