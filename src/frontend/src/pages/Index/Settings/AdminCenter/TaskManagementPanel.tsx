import { t } from '@lingui/macro';
import { Accordion } from '@mantine/core';
import { lazy } from 'react';

import { StylishText } from '../../../../components/items/StylishText';
import { Loadable } from '../../../../functions/loading';

const PendingTasksTable = Loadable(
  lazy(() => import('../../../../tables/settings/PendingTasksTable'))
);

const ScheduledTasksTable = Loadable(
  lazy(() => import('../../../../tables/settings/ScheduledTasksTable'))
);

const FailedTasksTable = Loadable(
  lazy(() => import('../../../../tables/settings/FailedTasksTable'))
);

export default function TaskManagementPanel() {
  return (
    <Accordion defaultValue="pending">
      <Accordion.Item value="pending">
        <Accordion.Control>
          <StylishText size="lg">{t`Pending Tasks`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <PendingTasksTable />
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value="scheduled">
        <Accordion.Control>
          <StylishText size="lg">{t`Scheduled Tasks`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <ScheduledTasksTable />
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value="failed">
        <Accordion.Control>
          <StylishText size="lg">{t`Failed Tasks`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <FailedTasksTable />
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
