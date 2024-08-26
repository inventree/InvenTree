import { t } from '@lingui/macro';
import { Accordion, Alert, Divider, Stack, Text } from '@mantine/core';
import { lazy } from 'react';

import { StylishText } from '../../../../components/items/StylishText';
import { FactCollection } from '../../../../components/settings/FactCollection';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { Loadable } from '../../../../functions/loading';
import { useInstance } from '../../../../hooks/UseInstance';

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
  const { instance: taskInfo } = useInstance({
    endpoint: ApiEndpoints.task_overview,
    hasPrimaryKey: false,
    refetchOnMount: true,
    defaultValue: {},
    updateInterval: 30 * 1000
  });

  return (
    <>
      {taskInfo?.is_running == false && (
        <Alert title={t`Background Worker Not Running`} color="red">
          <Text>{t`The background task manager service is not running. Contact your system administrator.`}</Text>
        </Alert>
      )}
      <Stack gap="xs">
        <FactCollection
          items={[
            { title: t`Pending Tasks`, value: taskInfo?.pending_tasks },
            { title: t`Scheduled Tasks`, value: taskInfo?.scheduled_tasks },
            { title: t`Failed Tasks`, value: taskInfo?.failed_tasks }
          ]}
        />
        <Divider />
        <Accordion defaultValue="pending">
          <Accordion.Item value="pending" key="pending-tasks">
            <Accordion.Control>
              <StylishText size="lg">{t`Pending Tasks`}</StylishText>
            </Accordion.Control>
            <Accordion.Panel>
              <PendingTasksTable />
            </Accordion.Panel>
          </Accordion.Item>
          <Accordion.Item value="scheduled" key="scheduled-tasks">
            <Accordion.Control>
              <StylishText size="lg">{t`Scheduled Tasks`}</StylishText>
            </Accordion.Control>
            <Accordion.Panel>
              <ScheduledTasksTable />
            </Accordion.Panel>
          </Accordion.Item>
          <Accordion.Item value="failed" key="failed-tasks">
            <Accordion.Control>
              <StylishText size="lg">{t`Failed Tasks`}</StylishText>
            </Accordion.Control>
            <Accordion.Panel>
              <FailedTasksTable />
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      </Stack>
    </>
  );
}
