import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  Accordion,
  ActionIcon,
  Alert,
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
import { IconExclamationCircle, IconRefresh } from '@tabler/icons-react';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { TableColumn } from '@lib/types/Tables';
import type { InvenTreeTableProps } from '@lib/types/Tables';
import { InfoItem } from '../../components/items/InfoItem';
import { StylishText } from '../../components/items/StylishText';
import { DetailDrawer } from '../../components/nav/DetailDrawer';
import { useTable } from '../../hooks/UseTable';
import { BooleanColumn, DescriptionColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
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

export function MachineDriverTable({
  machineType,
  prefix
}: {
  machineType?: string;
  prefix?: string;
}) {
  const navigate = useNavigate();
  const table = useTable('machine-drivers');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Name`
      },
      DescriptionColumn({}),
      {
        accessor: 'machine_type',
        title: t`Driver Type`
      },
      BooleanColumn({
        accessor: 'is_builtin',
        title: t`Builtin driver`
      })
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.machine_driver_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        enableDownload: false,
        enableSearch: false,
        onRowClick: (machine) => {
          navigate(`${prefix ?? '.'}/driver-${machine.slug}/`);
        },
        dataFormatter: (data: any) => {
          if (machineType) {
            return data.filter((d: any) => d.machine_type === machineType);
          }
          return data;
        }
      }}
    />
  );
}

function MachineTypeDrawer({
  machineTypeSlug
}: Readonly<{ machineTypeSlug: string }>) {
  const { machineTypes, isFetching } = useMachineTypeDriver({
    includeDrivers: false
  });
  const machineType = useMemo(
    () => machineTypes?.find((m) => m.slug === machineTypeSlug),
    [machineTypes, machineTypeSlug]
  );

  return (
    <>
      <Stack>
        <Group wrap='nowrap'>
          <StylishText size='md'>
            {machineType ? machineType.name : machineTypeSlug}
          </StylishText>
        </Group>

        {!machineType && (
          <Alert
            color='red'
            title={t`Not Found`}
            icon={<IconExclamationCircle />}
          >
            <Text>{t`Machine type not found.`}</Text>
          </Alert>
        )}

        <Accordion
          multiple
          defaultValue={['machine-type-info', 'machine-drivers']}
        >
          <Accordion.Item value='machine-type-info'>
            <Accordion.Control>
              <StylishText size='lg'>{t`Machine Type Information`}</StylishText>
            </Accordion.Control>
            <Accordion.Panel>
              <Card withBorder>
                <Stack pos='relative' gap='xs'>
                  <LoadingOverlay
                    visible={isFetching}
                    overlayProps={{ opacity: 0 }}
                  />
                  <InfoItem
                    name={t`Name`}
                    value={machineType?.name}
                    type='text'
                  />
                  <InfoItem
                    name={t`Slug`}
                    value={machineType?.slug}
                    type='text'
                  />
                  <InfoItem
                    name={t`Description`}
                    value={machineType?.description}
                    type='text'
                  />
                  {!machineType?.is_builtin && (
                    <InfoItem
                      name={t`Provider plugin`}
                      value={machineType?.provider_plugin?.name}
                      type='text'
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
                    type='code'
                  />
                  <InfoItem
                    name={t`Builtin`}
                    value={machineType?.is_builtin}
                    type='boolean'
                  />
                </Stack>
              </Card>
            </Accordion.Panel>
          </Accordion.Item>
          <Accordion.Item value='machine-drivers'>
            <Accordion.Control>
              <StylishText size='lg'>{t`Available Drivers`}</StylishText>
            </Accordion.Control>
            <Accordion.Panel>
              <Card withBorder>
                <MachineDriverTable machineType={machineTypeSlug} prefix='..' />
              </Card>
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      </Stack>
    </>
  );
}

function MachineDriverDrawer({
  machineDriverSlug
}: Readonly<{
  machineDriverSlug: string;
}>) {
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
      <Group justify='center'>
        <Title order={4}>
          {machineDriver ? machineDriver.name : machineDriverSlug}
        </Title>
      </Group>

      {!machineDriver && (
        <Text style={{ fontStyle: 'italic' }}>
          <Trans>Machine driver not found.</Trans>
        </Text>
      )}

      <Card withBorder>
        <Stack gap='md'>
          <Group justify='space-between'>
            <Title order={4}>
              <Trans>Machine driver information</Trans>
            </Title>
            <ActionIcon variant='outline' onClick={() => refresh()}>
              <IconRefresh />
            </ActionIcon>
          </Group>

          <Stack pos='relative' gap='xs'>
            <LoadingOverlay
              visible={isFetching}
              overlayProps={{ opacity: 0 }}
            />
            <InfoItem name={t`Name`} value={machineDriver?.name} type='text' />
            <InfoItem name={t`Slug`} value={machineDriver?.slug} type='text' />
            <InfoItem
              name={t`Description`}
              value={machineDriver?.description}
              type='text'
            />
            <InfoItem
              name={t`Machine type`}
              value={
                machineType ? machineType.name : machineDriver?.machine_type
              }
              type='text'
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
                type='text'
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
              type='code'
            />
            <InfoItem
              name={t`Builtin`}
              value={machineDriver?.is_builtin}
              type='boolean'
            />
            <Group justify='space-between' gap='xs'>
              <Text fz='sm' fw={700}>
                <Trans>Errors</Trans>:
              </Text>
              {machineDriver && machineDriver?.driver_errors.length > 0 ? (
                <Badge color='red' style={{ marginLeft: '10px' }}>
                  {machineDriver.driver_errors.length}
                </Badge>
              ) : (
                <Text fz='xs'>
                  <Trans>No errors reported</Trans>
                </Text>
              )}
              <List w='100%'>
                {machineDriver?.driver_errors.map((error, i) => (
                  <List.Item key={`${i}-${error}`}>
                    <Code>{error}</Code>
                  </List.Item>
                ))}
              </List>
            </Group>
          </Stack>
        </Stack>
      </Card>

      <Card withBorder>
        <Stack gap='md'>
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
}: Readonly<{
  props: InvenTreeTableProps;
}>) {
  const table = useTable('machineTypes');
  const navigate = useNavigate();

  const machineTypeTableColumns = useMemo<TableColumn<MachineTypeI>[]>(
    () => [
      {
        accessor: 'name',
        title: t`Name`
      },
      DescriptionColumn({}),
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
        title={t`Machine Type Detail`}
        size={'xl'}
        renderContent={(id) => {
          if (!id || !id.startsWith('type-')) return false;
          return (
            <MachineTypeDrawer machineTypeSlug={id.replace('type-', '')} />
          );
        }}
      />
      <DetailDrawer
        title={t`Machine Driver Detail`}
        size={'xl'}
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
          onRowClick: (machine) => navigate(`./type-${machine.slug}/`),
          params: {
            ...props.params
          }
        }}
      />
    </>
  );
}
