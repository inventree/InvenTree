import { t } from '@lingui/macro';
import { Drawer, Text } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useCallback, useMemo, useState } from 'react';

import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { openDeleteApiForm } from '../../../functions/forms';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { StylishText } from '../../items/StylishText';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction, RowDeleteAction } from '../RowActions';

/*
 * Table for display server error information
 */
export default function ErrorReportTable() {
  const table = useTable('error-report');

  const [error, setError] = useState<string>('');

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

  const rowActions = useCallback((record: any): RowAction[] => {
    return [
      RowDeleteAction({
        onClick: () => {
          openDeleteApiForm({
            url: ApiEndpoints.error_report_list,
            pk: record.pk,
            title: t`Delete error report`,
            onFormSuccess: table.refreshTable,
            successMessage: t`Error report deleted`,
            preFormWarning: t`Are you sure you want to delete this error report?`
          });
        }
      })
    ];
  }, []);

  return (
    <>
      <Drawer
        opened={opened}
        size="xl"
        position="right"
        title={<StylishText>{t`Error Details`}</StylishText>}
        onClose={close}
      >
        {error.split('\n').map((line: string) => {
          return <Text size="sm">{line}</Text>;
        })}
      </Drawer>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.error_report_list)}
        tableState={table}
        columns={columns}
        props={{
          enableBulkDelete: true,
          enableSelection: true,
          rowActions: rowActions,
          onRowClick: (row) => {
            setError(row.data);
            open();
          }
        }}
      />
    </>
  );
}
