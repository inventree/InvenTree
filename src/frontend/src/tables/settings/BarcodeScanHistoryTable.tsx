import { t } from '@lingui/macro';
import {
  Alert,
  Badge,
  Divider,
  Drawer,
  Group,
  Stack,
  Table,
  Text
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconExclamationCircle } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { CopyButton } from '../../components/buttons/CopyButton';
import { StylishText } from '../../components/items/StylishText';
import { RenderUser } from '../../components/render/User';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { shortenString } from '../../functions/tables';
import { useUserFilters } from '../../hooks/UseFilter';
import { useDeleteApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction } from '../RowActions';

/*
 * Render detail information for a particular barcode scan result.
 */
function BarcodeScanDetail({ scan }: { scan: any }) {
  return (
    <>
      <Stack gap="xs">
        <Table>
          <Table.Tbody>
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
              <Table.Th>{t`Status`}</Table.Th>
              <Table.Td>{scan.status}</Table.Td>
            </Table.Tr>
            {scan.response && (
              <Table.Tr>
                <Table.Td colSpan={2}>
                  <StylishText size="sm">{t`Response`}</StylishText>
                </Table.Td>
              </Table.Tr>
            )}
            {scan.response &&
              Object.keys(scan.response).map((key) => (
                <Table.Tr key={key}>
                  <Table.Th>{key}</Table.Th>
                  <Table.Td>
                    <Text
                      size="sm"
                      style={{
                        textWrap: 'wrap',
                        lineBreak: 'auto',
                        wordBreak: 'break-word'
                      }}
                    >
                      {scan.response[key]}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <CopyButton value={scan.response[key]} size="xs" />
                  </Table.Td>
                </Table.Tr>
              ))}
            {scan.context && (
              <Table.Tr>
                <Table.Td colSpan={2}>
                  <StylishText size="sm">{t`Context`}</StylishText>
                </Table.Td>
              </Table.Tr>
            )}
            {scan.context &&
              Object.keys(scan.context).map((key) => (
                <Table.Tr key={key}>
                  <Table.Th>{key}</Table.Th>
                  <Table.Td>
                    <Text
                      size="sm"
                      style={{
                        textWrap: 'wrap',
                        lineBreak: 'auto',
                        wordBreak: 'break-word'
                      }}
                    >
                      {scan.context[key]}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <CopyButton value={scan.context[key]} size="xs" />
                  </Table.Td>
                </Table.Tr>
              ))}
          </Table.Tbody>
        </Table>
      </Stack>
    </>
  );
}

/*
 * Display the barcode scan history table
 */
export default function BarcodeScanHistoryTable() {
  const user = useUserState();
  const table = useTable('barcode-history');

  const globalSettings = useGlobalSettingsState();

  const userFilters = useUserFilters();

  const [opened, { open, close }] = useDisclosure(false);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'timestamp',
        sortable: true,
        switchable: false,
        render: (record: any) => {
          return (
            <Group justify="space-between" wrap="nowrap">
              <Text>{record.timestamp}</Text>
              {record.user_detail && (
                <Badge size="xs">{record.user_detail.username}</Badge>
              )}
            </Group>
          );
        }
      },
      {
        accessor: 'data',
        sortable: true,
        switchable: true,
        render: (record: any) => {
          return (
            <Text
              size="xs"
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
        accessor: 'status',
        sortable: true
      }
    ];
  }, []);

  const filters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'user',
        label: t`User`,
        choices: userFilters.choices,
        description: t`Filter by user`
      }
    ];
  }, [userFilters]);

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
        size="xl"
        position="right"
        title={<StylishText>{t`Barcode Scan Details`}</StylishText>}
        onClose={close}
      >
        <BarcodeScanDetail scan={selectedResult} />
      </Drawer>
      <Stack gap="xs">
        {!globalSettings.isSet('BARCODE_STORE_RESULTS') && (
          <Alert
            color="red"
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
