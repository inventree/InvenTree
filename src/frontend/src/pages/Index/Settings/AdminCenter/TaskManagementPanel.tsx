import { t } from '@lingui/macro';
import { Accordion, Alert, Divider, Stack, Text } from '@mantine/core';
import { lazy } from 'react';

import { StylishText } from '../../../../components/items/StylishText';
import { FactCollection } from '../../../../components/settings/FactCollection';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { Loadable } from '../../../../functions/loading';
import { useInstance } from '../../../../hooks/UseInstance';
import FailedTasksTable from '../../../../tables/settings/FailedTasksTable';
import PendingTasksTable from '../../../../tables/settings/PendingTasksTable';

const ScheduledTasksTable = Loadable(
  lazy(() => import('../../../../tables/settings/ScheduledTasksTable'))
);

export default function TaskManagementPanel() {
  const { instance: taskInfo, refreshInstance: refreshTaskInfo } = useInstance({
    endpoint: ApiEndpoints.task_overview,
    hasPrimaryKey: false,
    refetchOnMount: true,
    defaultValue: {},
    updateInterval: 30 * 1000
  });

  return (
    <>
      {taskInfo?.is_running == false && (
        <Alert title={t`Background worker not running`} color='red'>
          <Text>{t`The background task manager service is not running. Contact your system administrator.`}</Text>
        </Alert>
      )}
      <Stack gap='xs'>
        <FactCollection
          items={[
            { title: t`Pending Tasks`, value: taskInfo?.pending_tasks },
            { title: t`Scheduled Tasks`, value: taskInfo?.scheduled_tasks },
            { title: t`Failed Tasks`, value: taskInfo?.failed_tasks }
          ]}
        />
        <Divider />
        <Accordion defaultValue='pending'>
          <Accordion.Item value='pending' key='pending-tasks'>
            <Accordion.Control>
              <StylishText size='lg'>{t`Pending Tasks`}</StylishText>
            </Accordion.Control>
            <Accordion.Panel>
              <PendingTasksTable onRecordsUpdated={refreshTaskInfo} />
            </Accordion.Panel>
          </Accordion.Item>
          <Accordion.Item value='scheduled' key='scheduled-tasks'>
            <Accordion.Control>
              <StylishText size='lg'>{t`Scheduled Tasks`}</StylishText>
            </Accordion.Control>
            <Accordion.Panel>
              <ScheduledTasksTable />
            </Accordion.Panel>
          </Accordion.Item>
          <Accordion.Item value='failed' key='failed-tasks'>
            <Accordion.Control>
              <StylishText size='lg'>{t`Failed Tasks`}</StylishText>
            </Accordion.Control>
            <Accordion.Panel>
              <FailedTasksTable onRecordsUpdated={refreshTaskInfo} />
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      </Stack>
    </>
  );
}
