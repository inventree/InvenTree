import { t } from '@lingui/core/macro';
import {
  Alert,
  Badge,
  Divider,
  Drawer,
  Group,
  type MantineStyleProp,
  Stack,
  Table,
  Text
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconExclamationCircle } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { RowDeleteAction } from '@lib/components/RowActions';
import { PassFailButton } from '@lib/components/YesNoButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { CopyButton } from '../../components/buttons/CopyButton';
import { StylishText } from '../../components/items/StylishText';
import { RenderUser } from '../../components/render/User';
import { shortenString } from '../../functions/tables';
import { useDeleteApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import { UserFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

/*
 * Render detail information for a particular barcode scan result.
 */
function BarcodeScanDetail({ scan }: Readonly<{ scan: any }>) {
  const dataStyle: MantineStyleProp = {
    textWrap: 'wrap',
    lineBreak: 'auto',
    wordBreak: 'break-word'
  };

  const hasResponseData = useMemo(() => {
    return scan.response && Object.keys(scan.response).length > 0;
  }, [scan.response]);

  const hasContextData = useMemo(() => {
    return scan.context && Object.keys(scan.context).length > 0;
  }, [scan.context]);

  return (
    <Stack gap='xs'>
      <Divider />
      <Table>
        <Table.Tbody>
          <Table.Tr>
            <Table.Td colSpan={2}>
              <StylishText size='sm'>{t`Barcode Information`}</StylishText>
            </Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Th>{t`Barcode`}</Table.Th>
            <Table.Td>
              <Text size='sm' style={dataStyle}>
                {scan.data}
              </Text>
            </Table.Td>
            <Table.Td>
              <CopyButton value={scan.data} size='xs' />
            </Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Th>{t`Timestamp`}</Table.Th>
            <Table.Td>{scan.timestamp}</Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Th>{t`User`}</Table.Th>
            <Table.Td>
              <RenderUser instance={scan.user_detail} />
            </Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Th>{t`Endpoint`}</Table.Th>
            <Table.Td>{scan.endpoint}</Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Th>{t`Result`}</Table.Th>
            <Table.Td>
              <PassFailButton value={scan.result} />
            </Table.Td>
          </Table.Tr>
          {hasContextData && (
            <Table.Tr>
              <Table.Td colSpan={2}>
                <StylishText size='sm'>{t`Context`}</StylishText>
              </Table.Td>
            </Table.Tr>
          )}
          {hasContextData &&
            Object.keys(scan.context).map((key) => (
              <Table.Tr key={key}>
                <Table.Th>{key}</Table.Th>
                <Table.Td>
                  <Text size='sm' style={dataStyle}>
                    {scan.context[key]}
                  </Text>
                </Table.Td>
                <Table.Td>
                  <CopyButton value={scan.context[key]} size='xs' />
                </Table.Td>
              </Table.Tr>
            ))}
          {hasResponseData && (
            <Table.Tr>
              <Table.Td colSpan={2}>
                <StylishText size='sm'>{t`Response`}</StylishText>
              </Table.Td>
            </Table.Tr>
          )}
          {hasResponseData &&
            Object.keys(scan.response).map((key) => (
              <Table.Tr key={key}>
                <Table.Th>{key}</Table.Th>
                <Table.Td>
                  <Text size='sm' style={dataStyle}>
                    {scan.response[key]}
                  </Text>
                </Table.Td>
                <Table.Td>
                  <CopyButton value={scan.response[key]} size='xs' />
                </Table.Td>
              </Table.Tr>
            ))}
        </Table.Tbody>
      </Table>
    </Stack>
  );
}

/*
 * Display the barcode scan history table
 */
export default function BarcodeScanHistoryTable() {
  const user = useUserState();
  const table = useTable('barcode-history');

  const globalSettings = useGlobalSettingsState();

  const [opened, { open, close }] = useDisclosure(false);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'timestamp',
        sortable: true,
        switchable: false,
        render: (record: any) => {
          return (
            <Group justify='space-between' wrap='nowrap'>
              <Text>{record.timestamp}</Text>
              {record.user_detail && (
                <Badge size='xs'>{record.user_detail.username}</Badge>
              )}
            </Group>
          );
        }
      },
      {
        accessor: 'data',
        sortable: false,
        switchable: true,
        render: (record: any) => {
          return (
            <Text
              size='xs'
              style={{
                textWrap: 'wrap',
                lineBreak: 'auto',
                wordBreak: 'break-word'
              }}
            >
              {shortenString({ str: record.data, len: 100 })}
            </Text>
          );
        }
      },
      {
        accessor: 'endpoint',
        sortable: true
      },
      {
        accessor: 'result',
        sortable: true,
        render: (record: any) => {
          return <PassFailButton value={record.result} />;
        }
      }
    ];
  }, []);

  const filters: TableFilter[] = useMemo(() => {
    return [
      UserFilter({}),
      {
        name: 'result',
        label: t`Result`,
        description: t`Filter by result`
      }
    ];
  }, []);

  const canDelete: boolean = useMemo(() => {
    return user.isStaff() && user.hasDeleteRole(UserRoles.admin);
  }, [user]);

  const [selectedResult, setSelectedResult] = useState<any>({});

  const deleteResult = useDeleteApiFormModal({
    url: ApiEndpoints.barcode_history,
    pk: selectedResult.pk,
    title: t`Delete Barcode Scan Record`,
    table: table
  });

  const rowActions = useCallback(
    (record: any) => {
      return [
        RowDeleteAction({
          hidden: !canDelete,
          onClick: () => {
            setSelectedResult(record);
            deleteResult.open();
          }
        })
      ];
    },
    [canDelete, user]
  );

  return (
    <>
      {deleteResult.modal}
      <Drawer
        opened={opened}
        size='xl'
        position='right'
        title={<StylishText>{t`Barcode Scan Details`}</StylishText>}
        onClose={close}
      >
        <BarcodeScanDetail scan={selectedResult} />
      </Drawer>
      <Stack gap='xs'>
        {!globalSettings.isSet('BARCODE_STORE_RESULTS') && (
          <Alert
            color='red'
            icon={<IconExclamationCircle />}
            title={t`Logging Disabled`}
          >
            <Text>{t`Barcode logging is not enabled`}</Text>
          </Alert>
        )}
        <InvenTreeTable
          url={apiUrl(ApiEndpoints.barcode_history)}
          tableState={table}
          columns={tableColumns}
          props={{
            tableFilters: filters,
            enableBulkDelete: canDelete,
            rowActions: rowActions,
            onRowClick: (row) => {
              setSelectedResult(row);
              open();
            }
          }}
        />
      </Stack>
    </>
  );
}
