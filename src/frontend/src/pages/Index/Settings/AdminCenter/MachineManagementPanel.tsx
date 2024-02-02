import { Trans } from '@lingui/macro';
import {
  ActionIcon,
  Code,
  Group,
  List,
  Space,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { IconRefresh } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';

import { api } from '../../../../App';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { apiUrl } from '../../../../states/ApiState';
import { MachineListTable } from '../../../../tables/machine/MachineListTable';
import { MachineTypeListTable } from '../../../../tables/machine/MachineTypeTable';

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

  return (
    <Stack>
      <MachineListTable props={{}} />

      <Space h="10px" />

      <Stack spacing={'xs'}>
        <Title order={5}>
          <Trans>Machine types</Trans>
        </Title>
        <MachineTypeListTable props={{}} />
      </Stack>

      <Space h="10px" />

      <Stack spacing={'xs'}>
        <Group>
          <Title order={5}>
            <Trans>Machine Error Stack</Trans>
          </Title>
          <ActionIcon variant="outline" onClick={() => refetch()}>
            <IconRefresh />
          </ActionIcon>
        </Group>
        {registryStatus?.registry_errors &&
        registryStatus.registry_errors.length === 0 ? (
          <Text italic>
            <Trans>There are no machine registry errors.</Trans>
          </Text>
        ) : (
          <List>
            {registryStatus?.registry_errors?.map((error, i) => (
              <List.Item key={i}>
                <Code>{error.message}</Code>
              </List.Item>
            ))}
          </List>
        )}
      </Stack>
    </Stack>
  );
}
