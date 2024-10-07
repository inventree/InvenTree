import { t } from '@lingui/macro';
import { Drawer, Group, Stack, Table, Text } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useCallback, useMemo, useState } from 'react';

import { CopyButton } from '../../components/buttons/CopyButton';
import { StylishText } from '../../components/items/StylishText';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { useDeleteApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction, RowDeleteAction } from '../RowActions';

function ErrorDetail({ error }: { error: any }) {
  return (
    <Stack gap="xs">
      <Table>
        <Table.Tbody>
          <Table.Tr>
            <Table.Th>{t`Message`}</Table.Th>
            <Table.Td>{error.info}</Table.Td>
            <Table.Td>
              <Group justify="right">
                <CopyButton value={error.info} size="sm" />
              </Group>
            </Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Th>{t`Timestamp`}</Table.Th>
            <Table.Td>{error.when}</Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Th>{t`Path`}</Table.Th>
            <Table.Td>{error.path}</Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Th>{t`Traceback`}</Table.Th>
            <Table.Td colSpan={2}>
              <Group justify="right">
                <CopyButton value={error.data} size="sm" />
              </Group>
            </Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td colSpan={2}>
              <Stack gap={3}>
                {error.data.split('\n').map((line: string, index: number) => (
                  <Text size="xs" key={`error-line-${index}`}>
                    {line}
                  </Text>
                ))}
              </Stack>
            </Table.Td>
          </Table.Tr>
        </Table.Tbody>
      </Table>
    </Stack>
  );
}

/*
 * Table for display server error information
 */
export default function ErrorReportTable() {
  const table = useTable('error-report');
  const user = useUserState();

  const [opened, { open, close }] = useDisclosure(false);

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'when',
        title: t`When`,
        sortable: true
      },
      {
        accessor: 'path',
        title: t`Path`,
        sortable: true
      },
      {
        accessor: 'info',
        title: t`Error Information`
      }
    ];
  }, []);

  const [selectedError, setSelectedError] = useState<any>({});

  const deleteErrorModal = useDeleteApiFormModal({
    url: ApiEndpoints.error_report_list,
    pk: selectedError.pk,
    title: t`Delete Error Report`,
    preFormContent: (
      <Text c="red">{t`Are you sure you want to delete this error report?`}</Text>
    ),
    successMessage: t`Error report deleted`,
    table: table
  });

  const rowActions = useCallback((record: any): RowAction[] => {
    return [
      RowDeleteAction({
        onClick: () => {
          setSelectedError(record);
          deleteErrorModal.open();
        }
      })
    ];
  }, []);

  return (
    <>
      {deleteErrorModal.modal}
      <Drawer
        opened={opened}
        size="xl"
        position="right"
        title={<StylishText>{t`Error Details`}</StylishText>}
        onClose={close}
      >
        <ErrorDetail error={selectedError} />
      </Drawer>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.error_report_list)}
        tableState={table}
        columns={columns}
        props={{
          enableBulkDelete: user.isStaff(),
          enableSelection: true,
          rowActions: rowActions,
          onRowClick: (row) => {
            setSelectedError(row);
            open();
          }
        }}
      />
    </>
  );
}
