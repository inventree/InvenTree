import { t } from '@lingui/macro';
import { useCallback, useMemo } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { openDeleteApiForm } from '../../../functions/forms';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction, RowDeleteAction } from '../RowActions';

/*
 * Table for display server error information
 */
export default function ErrorReportTable() {
  const table = useTable('error-report');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'when',
        title: t`When`
      },
      {
        accessor: 'path',
        title: t`Path`
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
            url: ApiPaths.error_report_list,
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
    <InvenTreeTable
      url={apiUrl(ApiPaths.error_report_list)}
      tableState={table}
      columns={columns}
      props={{
        rowActions: rowActions
      }}
    />
  );
}
