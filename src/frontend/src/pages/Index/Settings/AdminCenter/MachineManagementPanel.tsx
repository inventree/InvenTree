import { t } from '@lingui/core/macro';
import {
  Accordion,
  ActionIcon,
  Alert,
  Code,
  Group,
  List,
  Stack,
  Text
} from '@mantine/core';
import { IconInfoCircle, IconRefresh } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { api } from '../../../../App';
import { StylishText } from '../../../../components/items/StylishText';
import { GlobalSettingList } from '../../../../components/settings/SettingList';
import { MachineListTable } from '../../../../tables/machine/MachineListTable';
import {
  MachineDriverTable,
  MachineTypeListTable
} from '../../../../tables/machine/MachineTypeTable';

interface MachineRegistryStatusI {
  registry_errors: { message: string }[];
}

export default function MachineManagementPanel() {
  const { data: registryStatus, refetch } = useQuery<MachineRegistryStatusI>({
    queryKey: ['machine-registry-status'],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.machine_registry_status))
        .then((res) => res.data),
    staleTime: 10 * 1000
  });

  const hasErrors = useMemo(() => {
    return (
      registryStatus?.registry_errors &&
      registryStatus.registry_errors.length > 0
    );
  }, [registryStatus]);

  return (
    <Accordion multiple defaultValue={['machinelist']}>
      <Accordion.Item value='machinelist'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Machines`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <MachineListTable props={{}} />
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value='drivertypes'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Machine Drivers`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <MachineDriverTable />
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value='machinetypes'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Machine Types`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <MachineTypeListTable props={{}} />
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value='machineerrors'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Machine Errors`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <Stack gap='xs'>
            <Group
              justify='space-beteen'
              wrap='nowrap'
              style={{ width: '100%' }}
            >
              {hasErrors ? (
                <Alert
                  flex={10}
                  color='red'
                  title={t`Registry Registry Errors`}
                  icon={<IconInfoCircle />}
                >
                  <Text>{t`There are machine registry errors`}</Text>
                </Alert>
              ) : (
                <Alert
                  flex={10}
                  color='green'
                  title={t`Machine Registry Errors`}
                  icon={<IconInfoCircle />}
                >
                  <Text>{t`There are no machine registry errors`}</Text>
                </Alert>
              )}
              <ActionIcon variant='outline' onClick={() => refetch()}>
                <IconRefresh />
              </ActionIcon>
            </Group>
            {hasErrors && (
              <List>
                {registryStatus?.registry_errors?.map((error, i) => (
                  <List.Item key={i}>
                    <Code>{error.message}</Code>
                  </List.Item>
                ))}
              </List>
            )}
          </Stack>
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value='settings'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Machine Settings`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <GlobalSettingList keys={['MACHINE_PING_ENABLED']} />
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
