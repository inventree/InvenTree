import { Trans, t } from '@lingui/macro';
import {
  ActionIcon,
  Badge,
  Card,
  Code,
  Group,
  List,
  LoadingOverlay,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { IconRefresh } from '@tabler/icons-react';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { InfoItem } from '../../components/items/InfoItem';
import { DetailDrawer } from '../../components/nav/DetailDrawer';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { TableColumn } from '../Column';
import { BooleanColumn } from '../ColumnRenderers';
import { InvenTreeTable, InvenTreeTableProps } from '../InvenTreeTable';
import { MachineListTable, useMachineTypeDriver } from './MachineListTable';

export interface MachineTypeI {
  slug: string;
  name: string;
  description: string;
  provider_file: string;
  provider_plugin: { slug: string; name: string; pk: number | null } | null;
  is_builtin: boolean;
}

export interface MachineDriverI {
  slug: string;
  name: string;
  description: string;
  provider_file: string;
  provider_plugin: { slug: string; name: string; pk: number | null } | null;
  is_builtin: boolean;
  machine_type: string;
  driver_errors: string[];
}

function MachineTypeDrawer({ machineTypeSlug }: { machineTypeSlug: string }) {
  const navigate = useNavigate();

  const { machineTypes, refresh, isFetching } = useMachineTypeDriver({
    includeDrivers: false
  });
  const machineType = useMemo(
    () => machineTypes?.find((m) => m.slug === machineTypeSlug),
    [machineTypes, machineTypeSlug]
  );

  const table = useTable('machineDrivers');

  const machineDriverTableColumns = useMemo<TableColumn<MachineDriverI>[]>(
    () => [
      {
        accessor: 'name',
        title: t`Name`
      },
      {
        accessor: 'description',
        title: t`Description`
      },
      BooleanColumn({
        accessor: 'is_builtin',
        title: t`Builtin driver`
      })
    ],
    []
  );

  return (
    <Stack>
      <Group position="center">
        <Title order={4}>
          {machineType ? machineType.name : machineTypeSlug}
        </Title>
      </Group>

      {!machineType && (
        <Text italic>
          <Trans>Machine type not found.</Trans>
        </Text>
      )}

      <Card withBorder>
        <Stack spacing="md">
          <Group position="apart">
            <Title order={4}>
              <Trans>Machine type information</Trans>
            </Title>
            <ActionIcon variant="outline" onClick={() => refresh()}>
              <IconRefresh />
            </ActionIcon>
          </Group>

          <Stack pos="relative" spacing="xs">
            <LoadingOverlay visible={isFetching} overlayOpacity={0} />
            <InfoItem name={t`Name`} value={machineType?.name} type="text" />
            <InfoItem name={t`Slug`} value={machineType?.slug} type="text" />
            <InfoItem
              name={t`Description`}
              value={machineType?.description}
              type="text"
            />
            {!machineType?.is_builtin && (
              <InfoItem
                name={t`Provider plugin`}
                value={machineType?.provider_plugin?.name}
                type="text"
                link={
                  machineType?.provider_plugin?.pk !== null
                    ? `../../plugin/${machineType?.provider_plugin?.pk}/`
                    : undefined
                }
                detailDrawerLink
              />
            )}
            <InfoItem
              name={t`Provider file`}
              value={machineType?.provider_file}
              type="code"
            />
            <InfoItem
              name={t`Builtin`}
              value={machineType?.is_builtin}
              type="boolean"
            />
          </Stack>
        </Stack>
      </Card>

      <Card withBorder>
        <Stack spacing="md">
          <Title order={4}>
            <Trans>Available drivers</Trans>
          </Title>

          <InvenTreeTable
            url={apiUrl(ApiEndpoints.machine_driver_list)}
            tableState={table}
            columns={machineDriverTableColumns}
            props={{
              dataFormatter: (data: any) => {
                return data.filter(
                  (d: any) => d.machine_type === machineTypeSlug
                );
              },
              enableDownload: false,
              enableSearch: false,
              onRowClick: (machine) => navigate(`../driver-${machine.slug}/`)
            }}
          />
        </Stack>
      </Card>
    </Stack>
  );
}

function MachineDriverDrawer({
  machineDriverSlug
}: {
  machineDriverSlug: string;
}) {
  const { machineDrivers, machineTypes, refresh, isFetching } =
    useMachineTypeDriver();
  const machineDriver = useMemo(
    () => machineDrivers?.find((d) => d.slug === machineDriverSlug),
    [machineDrivers, machineDriverSlug]
  );
  const machineType = useMemo(
    () => machineTypes?.find((t) => t.slug === machineDriver?.machine_type),
    [machineDrivers, machineTypes]
  );

  return (
    <Stack>
      <Group position="center">
        <Title order={4}>
          {machineDriver ? machineDriver.name : machineDriverSlug}
        </Title>
      </Group>

      {!machineDriver && (
        <Text italic>
          <Trans>Machine driver not found.</Trans>
        </Text>
      )}

      <Card withBorder>
        <Stack spacing="md">
          <Group position="apart">
            <Title order={4}>
              <Trans>Machine driver information</Trans>
            </Title>
            <ActionIcon variant="outline" onClick={() => refresh()}>
              <IconRefresh />
            </ActionIcon>
          </Group>

          <Stack pos="relative" spacing="xs">
            <LoadingOverlay visible={isFetching} overlayOpacity={0} />
            <InfoItem name={t`Name`} value={machineDriver?.name} type="text" />
            <InfoItem name={t`Slug`} value={machineDriver?.slug} type="text" />
            <InfoItem
              name={t`Description`}
              value={machineDriver?.description}
              type="text"
            />
            <InfoItem
              name={t`Machine type`}
              value={
                machineType ? machineType.name : machineDriver?.machine_type
              }
              type="text"
              link={
                machineType
                  ? `../type-${machineDriver?.machine_type}`
                  : undefined
              }
              detailDrawerLink
            />
            {!machineDriver?.is_builtin && (
              <InfoItem
                name={t`Provider plugin`}
                value={machineDriver?.provider_plugin?.name}
                type="text"
                link={
                  machineDriver?.provider_plugin?.pk !== null
                    ? `../../plugin/${machineDriver?.provider_plugin?.pk}/`
                    : undefined
                }
                detailDrawerLink
              />
            )}
            <InfoItem
              name={t`Provider file`}
              value={machineDriver?.provider_file}
              type="code"
            />
            <InfoItem
              name={t`Builtin`}
              value={machineDriver?.is_builtin}
              type="boolean"
            />
            <Group position="apart" spacing="xs">
              <Text fz="sm" fw={700}>
                <Trans>Errors</Trans>:
              </Text>
              {machineDriver && machineDriver?.driver_errors.length > 0 ? (
                <Badge color="red" sx={{ marginLeft: '10px' }}>
                  {machineDriver.driver_errors.length}
                </Badge>
              ) : (
                <Text fz="xs">
                  <Trans>No errors reported</Trans>
                </Text>
              )}
              <List w="100%">
                {machineDriver?.driver_errors.map((error, i) => (
                  <List.Item key={i}>
                    <Code>{error}</Code>
                  </List.Item>
                ))}
              </List>
            </Group>
          </Stack>
        </Stack>
      </Card>

      <Card withBorder>
        <Stack spacing="md">
          <Title order={4}>
            <Trans>Machines</Trans>
          </Title>

          <MachineListTable
            props={{ params: { driver: machineDriverSlug } }}
            renderMachineDrawer={false}
            createProps={{
              machine_type: machineDriver?.machine_type,
              driver: machineDriverSlug
            }}
          />
        </Stack>
      </Card>
    </Stack>
  );
}

/**
 * Table displaying list of available machine types
 */
export function MachineTypeListTable({
  props
}: {
  props: InvenTreeTableProps;
}) {
  const table = useTable('machineTypes');
  const navigate = useNavigate();

  const machineTypeTableColumns = useMemo<TableColumn<MachineTypeI>[]>(
    () => [
      {
        accessor: 'name',
        title: t`Name`
      },
      {
        accessor: 'description',
        title: t`Description`
      },
      BooleanColumn({
        accessor: 'is_builtin',
        title: t`Builtin type`
      })
    ],
    []
  );

  return (
    <>
      <DetailDrawer
        title={t`Machine type detail`}
        size={'lg'}
        renderContent={(id) => {
          if (!id || !id.startsWith('type-')) return false;
          return (
            <MachineTypeDrawer machineTypeSlug={id.replace('type-', '')} />
          );
        }}
      />
      <DetailDrawer
        title={t`Machine driver detail`}
        size={'lg'}
        renderContent={(id) => {
          if (!id || !id.startsWith('driver-')) return false;
          return (
            <MachineDriverDrawer
              machineDriverSlug={id.replace('driver-', '')}
            />
          );
        }}
      />
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.machine_types_list)}
        tableState={table}
        columns={machineTypeTableColumns}
        props={{
          ...props,
          enableDownload: false,
          enableSearch: false,
          onRowClick: (machine) => navigate(`type-${machine.slug}/`),
          params: {
            ...props.params
          }
        }}
      />
    </>
  );
}
