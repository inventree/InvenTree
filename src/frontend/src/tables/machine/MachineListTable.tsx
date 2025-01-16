import { Trans, t } from '@lingui/macro';
import {
  Accordion,
  Badge,
  Box,
  Card,
  Code,
  Flex,
  Group,
  Indicator,
  List,
  LoadingOverlay,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconCheck, IconRefresh } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { YesNoButton } from '../../components/buttons/YesNoButton';
import {
  DeleteItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import { InfoItem } from '../../components/items/InfoItem';
import { StylishText } from '../../components/items/StylishText';
import { UnavailableIndicator } from '../../components/items/UnavailableIndicator';
import {
  DetailDrawer,
  DetailDrawerLink
} from '../../components/nav/DetailDrawer';
import {
  StatusRenderer,
  TableStatusRenderer
} from '../../components/render/StatusRenderer';
import { MachineSettingList } from '../../components/settings/SettingList';
import { useApi } from '../../contexts/ApiContext';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import type { TableColumn } from '../Column';
import { BooleanColumn } from '../ColumnRenderers';
import { InvenTreeTable, type InvenTreeTableProps } from '../InvenTreeTable';
import type { MachineDriverI, MachineTypeI } from './MachineTypeTable';

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
  restart_required: boolean;
}

function MachineStatusIndicator({ machine }: Readonly<{ machine: MachineI }>) {
  const style = { marginLeft: '4px' };

  // machine is not active, show a gray dot
  if (!machine.active) {
    return (
      <Indicator style={style} color='gray'>
        <Box />
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
    <Indicator processing={processing} style={style} color={color}>
      <Box />
    </Indicator>
  );
}

export function useMachineTypeDriver({
  includeTypes = true,
  includeDrivers = true
}: { includeTypes?: boolean; includeDrivers?: boolean } = {}) {
  const api = useApi();

  const {
    data: machineTypes,
    isFetching: isMachineTypesFetching,
    refetch: refreshMachineTypes
  } = useQuery<MachineTypeI[]>({
    enabled: includeTypes,
    queryKey: ['machine-types'],
    queryFn: () =>
      api.get(apiUrl(ApiEndpoints.machine_types_list)).then((res) => res.data),
    staleTime: 10 * 1000
  });
  const {
    data: machineDrivers,
    isFetching: isMachineDriversFetching,
    refetch: refreshDrivers
  } = useQuery<MachineDriverI[]>({
    enabled: includeDrivers,
    queryKey: ['machine-drivers'],
    queryFn: () =>
      api.get(apiUrl(ApiEndpoints.machine_driver_list)).then((res) => res.data),
    staleTime: 10 * 1000
  });

  const refresh = useCallback(() => {
    refreshMachineTypes();
    refreshDrivers();
  }, [refreshDrivers, refreshMachineTypes]);

  return {
    machineTypes,
    machineDrivers,
    isFetching: isMachineTypesFetching || isMachineDriversFetching,
    refresh
  };
}

function MachineDrawer({
  machinePk,
  refreshTable
}: Readonly<{
  machinePk: string;
  refreshTable: () => void;
}>) {
  const api = useApi();
  const navigate = useNavigate();
  const {
    data: machine,
    refetch,
    isFetching: isMachineFetching
  } = useQuery<MachineI>({
    enabled: true,
    queryKey: ['machine-detail', machinePk],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.machine_list, machinePk))
        .then((res) => res.data)
  });
  const {
    machineTypes,
    machineDrivers,
    isFetching: isMachineTypeDriverFetching
  } = useMachineTypeDriver();

  const isFetching = isMachineFetching || isMachineTypeDriverFetching;

  const machineType = useMemo(
    () =>
      machineTypes && machine
        ? machineTypes.find((t) => t.slug === machine.machine_type)
        : undefined,
    [machine?.machine_type, machineTypes]
  );

  const machineDriver = useMemo(
    () =>
      machineDrivers && machine
        ? machineDrivers.find((d) => d.slug === machine.driver)
        : undefined,
    [machine?.driver, machineDrivers]
  );

  const refreshAll = useCallback(() => {
    refetch();
    refreshTable();
  }, [refetch, refreshTable]);

  const restartMachine = useCallback(
    (machinePk: string) => {
      api
        .post(
          apiUrl(ApiEndpoints.machine_restart, undefined, {
            machine: machinePk
          })
        )
        .then(() => {
          refreshAll();
          notifications.show({
            message: t`Machine restarted`,
            color: 'green',
            icon: <IconCheck size='1rem' />
          });
        });
    },
    [refreshAll]
  );

  const machineEditModal = useEditApiFormModal({
    title: t`Edit machine`,
    url: ApiEndpoints.machine_list,
    pk: machinePk,
    fields: useMemo(
      () => ({
        name: {},
        active: {}
      }),
      []
    ),
    onClose: () => refreshAll()
  });

  const machineDeleteModal = useDeleteApiFormModal({
    title: t`Delete machine`,
    successMessage: t`Machine successfully deleted.`,
    url: ApiEndpoints.machine_list,
    pk: machinePk,
    preFormContent: (
      <Text>{t`Are you sure you want to remove the machine "${machine?.name}"?`}</Text>
    ),
    onFormSuccess: () => {
      refreshTable();
      navigate(-1);
    }
  });

  return (
    <>
      <Stack gap='xs'>
        {machineEditModal.modal}
        {machineDeleteModal.modal}

        <Group justify='space-between'>
          <Group>
            {machine && <MachineStatusIndicator machine={machine} />}
            <Title order={4}>{machine?.name}</Title>
          </Group>

          <Group>
            {machine?.restart_required && (
              <Badge color='red'>
                <Trans>Restart required</Trans>
              </Badge>
            )}
            <OptionsActionDropdown
              tooltip={t`Machine Actions`}
              actions={[
                EditItemAction({
                  tooltip: t`Edit machine`,
                  onClick: machineEditModal.open
                }),
                DeleteItemAction({
                  tooltip: t`Delete machine`,
                  onClick: machineDeleteModal.open
                }),
                {
                  icon: <IconRefresh />,
                  name: t`Restart`,
                  tooltip:
                    t`Restart machine` +
                    (machine?.restart_required
                      ? ` (${t`manual restart required`})`
                      : ''),
                  indicator: machine?.restart_required
                    ? { color: 'red' }
                    : undefined,
                  onClick: () => machine && restartMachine(machine?.pk)
                }
              ]}
            />
          </Group>
        </Group>

        <Accordion
          multiple
          defaultValue={['machine-info', 'machine-settings', 'driver-settings']}
        >
          <Accordion.Item value='machine-info'>
            <Accordion.Control>
              <StylishText size='lg'>{t`Machine Information`}</StylishText>
            </Accordion.Control>
            <Accordion.Panel>
              <Card withBorder>
                <Stack gap='md'>
                  <Stack pos='relative' gap='xs'>
                    <LoadingOverlay
                      visible={isFetching}
                      overlayProps={{ opacity: 0 }}
                    />
                    <InfoItem name={t`Machine Type`}>
                      <Group gap='xs'>
                        {machineType ? (
                          <DetailDrawerLink
                            to={`../type-${machine?.machine_type}`}
                            text={machineType.name}
                          />
                        ) : (
                          <Text>{machine?.machine_type}</Text>
                        )}
                        {machine && !machineType && <UnavailableIndicator />}
                      </Group>
                    </InfoItem>
                    <InfoItem name={t`Machine Driver`}>
                      <Group gap='xs'>
                        {machineDriver ? (
                          <DetailDrawerLink
                            to={`../driver-${machine?.driver}`}
                            text={machineDriver.name}
                          />
                        ) : (
                          <Text>{machine?.driver}</Text>
                        )}
                        {!machine?.is_driver_available && (
                          <UnavailableIndicator />
                        )}
                      </Group>
                    </InfoItem>
                    <InfoItem name={t`Initialized`}>
                      <YesNoButton value={machine?.initialized || false} />
                    </InfoItem>
                    <InfoItem name={t`Active`}>
                      <YesNoButton value={machine?.active || false} />
                    </InfoItem>
                    <InfoItem name={t`Status`}>
                      <Flex direction='column'>
                        {machine?.status === -1 ? (
                          <Text fz='xs'>No status</Text>
                        ) : (
                          StatusRenderer({
                            status: `${machine?.status || -1}`,
                            type: `MachineStatus__${machine?.status_model}` as any
                          })
                        )}
                        <Text fz='sm'>{machine?.status_text}</Text>
                      </Flex>
                    </InfoItem>
                    <Group justify='space-between' gap='xs'>
                      <Text fz='sm' fw={700}>
                        <Trans>Errors</Trans>:
                      </Text>
                      {machine && machine?.machine_errors.length > 0 ? (
                        <Badge color='red' style={{ marginLeft: '10px' }}>
                          {machine?.machine_errors.length}
                        </Badge>
                      ) : (
                        <Text fz='xs'>
                          <Trans>No errors reported</Trans>
                        </Text>
                      )}
                      <List w='100%'>
                        {machine?.machine_errors.map((error, i) => (
                          <List.Item key={i}>
                            <Code>{error}</Code>
                          </List.Item>
                        ))}
                      </List>
                    </Group>
                  </Stack>
                </Stack>
              </Card>
            </Accordion.Panel>
          </Accordion.Item>
          {machine?.is_driver_available && (
            <Accordion.Item value='machine-settings'>
              <Accordion.Control>
                <StylishText size='lg'>{t`Machine Settings`}</StylishText>
              </Accordion.Control>
              <Accordion.Panel>
                <Card withBorder>
                  <MachineSettingList
                    machinePk={machinePk}
                    configType='M'
                    onChange={refreshAll}
                  />
                </Card>
              </Accordion.Panel>
            </Accordion.Item>
          )}
          {machine?.is_driver_available && (
            <Accordion.Item value='driver-settings'>
              <Accordion.Control>
                <StylishText size='lg'>{t`Driver Settings`}</StylishText>
              </Accordion.Control>
              <Accordion.Panel>
                <Card withBorder>
                  <MachineSettingList
                    machinePk={machinePk}
                    configType='D'
                    onChange={refreshAll}
                  />
                </Card>
              </Accordion.Panel>
            </Accordion.Item>
          )}
        </Accordion>
      </Stack>
    </>
  );
}

/**
 * Table displaying list of available plugins
 */
export function MachineListTable({
  props,
  renderMachineDrawer = true,
  createProps
}: Readonly<{
  props: InvenTreeTableProps;
  renderMachineDrawer?: boolean;
  createProps?: { machine_type?: string; driver?: string };
}>) {
  const { machineTypes, machineDrivers } = useMachineTypeDriver();

  const table = useTable('machine');
  const navigate = useNavigate();

  const machineTableColumns = useMemo<TableColumn<MachineI>[]>(
    () => [
      {
        accessor: 'name',
        sortable: true,
        render: (record) => (
          <Group justify='left' wrap='nowrap'>
            <MachineStatusIndicator machine={record} />
            <Text>{record.name}</Text>
            {record.restart_required && (
              <Badge color='red'>
                <Trans>Restart required</Trans>
              </Badge>
            )}
          </Group>
        )
      },
      {
        accessor: 'machine_type',
        sortable: true,
        render: (record) => {
          const machineType = machineTypes?.find(
            (m) => m.slug === record.machine_type
          );
          return (
            <Group gap='xs'>
              <Text>
                {machineType ? machineType.name : record.machine_type}
              </Text>
              {machineTypes && !machineType && <UnavailableIndicator />}
            </Group>
          );
        }
      },
      {
        accessor: 'driver',
        sortable: true,
        render: (record) => {
          const driver = machineDrivers?.find((d) => d.slug === record.driver);
          return (
            <Group gap='xs'>
              <Text>{driver ? driver.name : record.driver}</Text>
              {!record.is_driver_available && <UnavailableIndicator />}
            </Group>
          );
        }
      },
      BooleanColumn({
        accessor: 'initialized'
      }),
      BooleanColumn({
        accessor: 'active'
      }),
      {
        accessor: 'status',
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
        display_name: d.name
      }));
  }, [machineDrivers, createFormMachineType]);

  const createMachineForm = useCreateApiFormModal({
    title: t`Add machine`,
    url: ApiEndpoints.machine_list,
    fields: {
      name: {},
      machine_type: {
        hidden: !!createProps?.machine_type,
        ...(createProps?.machine_type
          ? { value: createProps.machine_type }
          : {}),
        field_type: 'choice',
        choices: machineTypes
          ? machineTypes.map((t) => ({
              value: t.slug,
              display_name: t.name
            }))
          : [],
        onValueChange: (value) => setCreateFormMachineType(value)
      },
      driver: {
        hidden: !!createProps?.driver,
        ...(createProps?.driver ? { value: createProps.driver } : {}),
        field_type: 'choice',
        disabled: !createFormMachineType,
        choices: createFormDriverOptions
      },
      active: {}
    },
    onFormSuccess: (data) => {
      table.refreshTable();
      navigate(
        renderMachineDrawer ? `machine-${data.pk}/` : `../machine-${data.pk}/`
      );
    },
    onClose: () => {
      setCreateFormMachineType(null);
    }
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-machine'
        tooltip={t`Add machine`}
        onClick={() => {
          setCreateFormMachineType(null);
          createMachineForm.open();
        }}
      />
    ];
  }, [createMachineForm.open]);

  return (
    <>
      {createMachineForm.modal}
      {renderMachineDrawer && (
        <DetailDrawer
          title={t`Machine Detail`}
          size={'xl'}
          renderContent={(id) => {
            if (!id || !id.startsWith('machine-')) return false;
            return (
              <MachineDrawer
                machinePk={id.replace('machine-', '')}
                refreshTable={table.refreshTable}
              />
            );
          }}
        />
      )}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.machine_list)}
        tableState={table}
        columns={machineTableColumns}
        props={{
          ...props,
          enableDownload: false,
          onRowClick: (machine) =>
            navigate(
              renderMachineDrawer
                ? `machine-${machine.pk}/`
                : `../machine-${machine.pk}/`
            ),
          tableActions,
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
              label: t`Driver`,
              type: 'choice',
              choiceFunction: () =>
                machineDrivers
                  ? machineDrivers.map((d) => ({
                      value: d.slug,
                      label: d.name
                    }))
                  : []
            }
          ]
        }}
      />
    </>
  );
}
