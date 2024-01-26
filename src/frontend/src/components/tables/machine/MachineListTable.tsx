import { Trans, t } from '@lingui/macro';
import {
  ActionIcon,
  Badge,
  Box,
  Card,
  Code,
  Flex,
  Group,
  Indicator,
  List,
  LoadingOverlay,
  Space,
  Stack,
  Text,
  Title,
  Tooltip
} from '@mantine/core';
import { IconChevronLeft, IconDots, IconRefresh } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import React, { useCallback, useMemo, useState } from 'react';

import { api } from '../../../App';
import { ApiPaths } from '../../../enums/ApiEndpoints';
import {
  OpenApiFormProps,
  openCreateApiForm,
  openDeleteApiForm,
  openEditApiForm
} from '../../../functions/forms';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { AddItemButton } from '../../buttons/AddItemButton';
import {
  ActionDropdown,
  DeleteItemAction,
  EditItemAction
} from '../../items/ActionDropdown';
import { UnavailableIndicator } from '../../items/UnavailableIndicator';
import { YesNoButton } from '../../items/YesNoButton';
import {
  StatusRenderer,
  TableStatusRenderer
} from '../../render/StatusRenderer';
import { MachineSettingList } from '../../settings/SettingList';
import { TableColumn } from '../Column';
import { BooleanColumn } from '../ColumnRenderers';
import { InvenTreeTable, InvenTreeTableProps } from '../InvenTreeTable';

interface MachineI {
  pk: string;
  name: string;
  machine_type: string;
  driver: string;
  initialized: boolean;
  active: boolean;
  status: number;
  status_model: string;
  status_text: string;
  machine_errors: string[];
  is_driver_available: boolean;
}

interface MachineTypeI {
  slug: string;
  name: string;
  description: string;
  provider_file: string;
  provider_plugin: string;
  is_builtin: boolean;
}

interface MachineDriverI {
  slug: string;
  name: string;
  description: string;
  provider_file: string;
  provider_plugin: string;
  is_builtin: boolean;
  machine_type: string;
}

function MachineStatusIndicator({ machine }: { machine: MachineI }) {
  const sx = { marginLeft: '4px' };

  // machine is not active, show a gray dot
  if (!machine.active) {
    return (
      <Indicator sx={sx} color="gray">
        <Box></Box>
      </Indicator>
    );
  }

  // determine the status color
  let color = 'green';
  const hasErrors =
    machine.machine_errors.length > 0 || !machine.is_driver_available;

  if (hasErrors || machine.status >= 300) color = 'red';
  else if (machine.status >= 200) color = 'orange';

  // determine if the machine is running
  const processing =
    machine.initialized && machine.status > 0 && machine.status < 300;

  return (
    <Indicator processing={processing} sx={sx} color={color}>
      <Box></Box>
    </Indicator>
  );
}

function MachineDetail({
  machinePk,
  goBack
}: {
  machinePk: string;
  goBack: () => void;
}) {
  const {
    data: machine,
    refetch,
    isFetching: isMachineFetching
  } = useQuery<MachineI>({
    enabled: true,
    queryKey: ['machine-detail', machinePk],
    queryFn: () =>
      api.get(apiUrl(ApiPaths.machine_list, machinePk)).then((res) => res.data)
  });
  const { data: machineTypes, isFetching: isMachineTypesFetching } = useQuery<
    MachineTypeI[]
  >({
    queryKey: ['machine-types'],
    queryFn: () =>
      api.get(apiUrl(ApiPaths.machine_types_list)).then((res) => res.data),
    staleTime: 10 * 1000
  });

  const isFetching = isMachineFetching || isMachineTypesFetching;

  function InfoItem({
    name,
    children
  }: {
    name: string;
    children: React.ReactNode;
  }) {
    return (
      <Group position="apart">
        <Text fz="sm" fw={700}>
          {name}:
        </Text>
        <Flex>{children}</Flex>
      </Group>
    );
  }

  return (
    <Stack spacing="xs">
      <Group position="apart">
        <Tooltip label={t`Back`}>
          <ActionIcon onClick={goBack} variant="outline">
            <IconChevronLeft />
          </ActionIcon>
        </Tooltip>

        <Group>
          {machine && <MachineStatusIndicator machine={machine} />}
          <Title order={4}>{machine?.name}</Title>
        </Group>

        <ActionDropdown
          tooltip={t`Machine Actions`}
          icon={<IconDots />}
          actions={[
            EditItemAction({
              tooltip: t`Edit machine`,
              onClick: () => {
                openEditApiForm({
                  title: t`Edit machine`,
                  url: ApiPaths.machine_list,
                  pk: machinePk,
                  fields: {
                    name: {},
                    active: {}
                  },
                  onClose: () => refetch()
                });
              }
            }),
            DeleteItemAction({
              tooltip: t`Delete machine`,
              onClick: () => {
                openDeleteApiForm({
                  title: t`Delete machine`,
                  successMessage: t`Machine successfully deleted.`,
                  url: ApiPaths.machine_list,
                  pk: machinePk,
                  preFormContent: (
                    <Text>{t`Are you sure you want to remove the machine "${machine?.name}"?`}</Text>
                  ),
                  onFormSuccess: () => goBack()
                });
              }
            })
          ]}
        />
      </Group>

      <Card maw={350}>
        <Stack spacing="md">
          <Group position="apart">
            <Title order={4}>
              <Trans>Info</Trans>
            </Title>
            <ActionIcon variant="outline" onClick={() => refetch()}>
              <IconRefresh />
            </ActionIcon>
          </Group>
          <Stack pos="relative" spacing="xs">
            <LoadingOverlay visible={isFetching} overlayOpacity={0} />
            <InfoItem name={t`Machine Type`}>
              <Group spacing="xs">
                <Text>{machine?.machine_type}</Text>
                {machine &&
                  machineTypes &&
                  machineTypes.findIndex(
                    (m) => m.slug === machine.machine_type
                  ) === -1 && <UnavailableIndicator />}
              </Group>
            </InfoItem>
            <InfoItem name={t`Machine Driver`}>
              <Group spacing="xs">
                <Text>{machine?.driver}</Text>
                {!machine?.is_driver_available && <UnavailableIndicator />}
              </Group>
            </InfoItem>
            <InfoItem name={t`Initialized`}>
              <YesNoButton value={machine?.initialized || false} />
            </InfoItem>
            <InfoItem name={t`Active`}>
              <YesNoButton value={machine?.active || false} />
            </InfoItem>
            <InfoItem name={t`Status`}>
              <Flex direction="column">
                {machine?.status === -1 ? (
                  <Text fz="xs">No status</Text>
                ) : (
                  StatusRenderer({
                    status: `${machine?.status || -1}`,
                    type: `MachineStatus__${machine?.status_model}` as any
                  })
                )}
                <Text fz="sm">{machine?.status_text}</Text>
              </Flex>
            </InfoItem>
            <Group position="apart" spacing="xs">
              <Text fz="sm" fw={700}>
                <Trans>Errors</Trans>:
              </Text>
              {machine && machine?.machine_errors.length > 0 ? (
                <Badge color="red" sx={{ marginLeft: '10px' }}>
                  {machine?.machine_errors.length}
                </Badge>
              ) : (
                <Text fz="xs">
                  <Trans>No errors reported</Trans>
                </Text>
              )}
              <List w="100%">
                {machine?.machine_errors.map((error) => (
                  <List.Item key={error}>
                    <Code>{error}</Code>
                  </List.Item>
                ))}
              </List>
            </Group>
          </Stack>
        </Stack>
      </Card>
      <Space h="10px" />

      {machine?.is_driver_available && (
        <>
          <Title order={5}>
            <Trans>Machine Settings</Trans>
          </Title>
          <MachineSettingList machinePk={machinePk} configType="M" />

          <Title order={5}>
            <Trans>Driver Settings</Trans>
          </Title>
          <MachineSettingList machinePk={machinePk} configType="D" />
        </>
      )}
    </Stack>
  );
}

/**
 * Table displaying list of available plugins
 */
export function MachineListTable({ props }: { props: InvenTreeTableProps }) {
  const { data: machineTypes } = useQuery<MachineTypeI[]>({
    queryKey: ['machine-types'],
    queryFn: () =>
      api.get(apiUrl(ApiPaths.machine_types_list)).then((res) => res.data),
    staleTime: 10 * 1000
  });
  const { data: machineDrivers } = useQuery<MachineDriverI[]>({
    queryKey: ['machine-drivers'],
    queryFn: () =>
      api.get(apiUrl(ApiPaths.machine_driver_list)).then((res) => res.data),
    staleTime: 10 * 1000
  });

  const table = useTable('machine');

  const machineTableColumns = useMemo<TableColumn<MachineI>[]>(
    () => [
      {
        accessor: 'name',
        title: t`Machine`,
        sortable: true,
        render: function (record) {
          return (
            <Group position="left">
              <MachineStatusIndicator machine={record} />
              <Text>{record.name}</Text>
            </Group>
          );
        }
      },
      {
        accessor: 'machine_type',
        title: t`Machine Type`,
        sortable: true,
        render: (record) => {
          return (
            <Group spacing="xs">
              <Text>{record.machine_type}</Text>
              {machineTypes &&
                machineTypes.findIndex(
                  (m: any) => m.slug === record.machine_type
                ) === -1 && <UnavailableIndicator />}
            </Group>
          );
        }
      },
      {
        accessor: 'driver',
        title: t`Machine Driver`,
        sortable: true,
        render: (record) => {
          return (
            <Group spacing="xs">
              <Text>{record.driver}</Text>
              {!record.is_driver_available && <UnavailableIndicator />}
            </Group>
          );
        }
      },
      BooleanColumn({
        accessor: 'initialized',
        title: t`Initialized`
      }),
      BooleanColumn({
        accessor: 'active',
        title: t`Active`
      }),
      {
        accessor: 'status',
        title: t`Status`,
        sortable: false,
        render: (record) => {
          const renderer = TableStatusRenderer(
            `MachineStatus__${record.status_model}` as any
          );
          if (renderer && record.status !== -1) {
            return renderer(record);
          }
        }
      }
    ],
    [machineTypes]
  );

  const [createFormMachineType, setCreateFormMachineType] = useState<
    null | string
  >(null);
  const createFormDriverOptions = useMemo(() => {
    if (!machineDrivers) return [];

    return machineDrivers
      .filter((d) => d.machine_type === createFormMachineType)
      .map((d) => ({
        value: d.slug,
        display_name: `${d.name} (${d.description})`
      }));
  }, [machineDrivers, createFormMachineType]);

  const createMachineForm = useMemo<OpenApiFormProps>(() => {
    return {
      title: t`Create machine`,
      url: ApiPaths.machine_list,
      fields: {
        name: {},
        machine_type: {
          field_type: 'choice',
          choices: machineTypes
            ? machineTypes.map((t) => ({
                value: t.slug,
                display_name: `${t.name} (${t.description})`
              }))
            : [],
          onValueChange: ({ value }) => setCreateFormMachineType(value)
        },
        driver: {
          field_type: 'choice',
          disabled: !createFormMachineType,
          choices: createFormDriverOptions
        },
        active: {}
      },
      onClose: () => {
        setCreateFormMachineType(null);
      }
    };
  }, [createFormMachineType, createFormDriverOptions, machineTypes]);

  const [currentMachinePk, setCurrentMachinePk] = useState<null | string>(null);
  const goBack = useCallback(() => setCurrentMachinePk(null), []);

  if (currentMachinePk) {
    return <MachineDetail machinePk={currentMachinePk} goBack={goBack} />;
  }

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.machine_list)}
      tableState={table}
      columns={machineTableColumns}
      props={{
        ...props,
        enableDownload: false,
        onRowClick: (record) => setCurrentMachinePk(record.pk),
        tableActions: [
          <AddItemButton
            variant="outline"
            onClick={() => {
              setCreateFormMachineType(null);
              openCreateApiForm(createMachineForm);
            }}
          />
        ],
        params: {
          ...props.params
        },
        tableFilters: [
          {
            name: 'active',
            label: t`Active`,
            type: 'boolean'
          },
          {
            name: 'machine_type',
            label: t`Machine Type`,
            type: 'choice',
            choiceFunction: () =>
              machineTypes
                ? machineTypes.map((t) => ({ value: t.slug, label: t.name }))
                : []
          },
          {
            name: 'driver',
            label: t`Machine Driver`,
            type: 'choice',
            choiceFunction: () =>
              machineDrivers
                ? machineDrivers.map((d) => ({ value: d.slug, label: d.name }))
                : []
          }
        ]
      }}
    />
  );
}
