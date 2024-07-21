import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';

import PermissionDenied from '../../components/errors/PermissionDenied';
import { PageDetail } from '../../components/nav/PageDetail';
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

  return (
    <Stack>
      <PageDetail title={t`Build Orders`} actions={[]} />
      <BuildOrderTable />
    </Stack>
  );
}
