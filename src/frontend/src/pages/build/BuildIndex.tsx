import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import { IconTools } from '@tabler/icons-react';
import { useMemo } from 'react';

import PermissionDenied from '../../components/errors/PermissionDenied';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/panels/PanelGroup';
import { UserRoles } from '../../enums/Roles';
import { useUserState } from '../../states/UserState';
import { BuildOrderTable } from '../../tables/build/BuildOrderTable';

/**
 * Build Order index page
 */
export default function BuildIndex() {
  const user = useUserState();

  if (!user.isLoggedIn() || !user.hasViewRole(UserRoles.build)) {
    return <PermissionDenied />;
  }

  const panels = useMemo(() => {
    return [
      {
        name: 'buildorders',
        label: t`Build Orders`,
        content: <BuildOrderTable />,
        icon: <IconTools />
      }
    ];
  }, []);

  return (
    <Stack>
      <PageDetail title={t`Manufacturing`} actions={[]} />
      <PanelGroup
        pageKey='build-index'
        panels={panels}
        model='manufacturing'
        id={null}
      />
    </Stack>
  );
}
