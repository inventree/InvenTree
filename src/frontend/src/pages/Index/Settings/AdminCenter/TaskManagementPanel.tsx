import { t } from '@lingui/macro';
import { Divider, Stack } from '@mantine/core';
import { lazy } from 'react';

import { StylishText } from '../../../../components/items/StylishText';
import { Loadable } from '../../../../functions/loading';

const PendingTasksTable = Loadable(
  lazy(() => import('../../../../components/tables/settings/PendingTasksTable'))
);

const ScheduledTasksTable = Loadable(
  lazy(
    () => import('../../../../components/tables/settings/ScheduledTasksTable')
  )
);

export default function TaskManagementPanel() {
  return (
    <Stack>
      <StylishText size="lg">{t`Pending Tasks`}</StylishText>
      <PendingTasksTable />
      <Divider />
      <StylishText size="lg">{t`Scheduled Tasks`}</StylishText>
      <ScheduledTasksTable />
      <Divider />
      <StylishText size="lg">{t`Failed Tasks`}</StylishText>
    </Stack>
  );
}
