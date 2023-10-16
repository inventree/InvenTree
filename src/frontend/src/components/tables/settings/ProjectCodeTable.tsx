import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { notYetImplemented } from '../../../functions/notifications';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction } from '../RowActions';

/**
 * Table for displaying list of project codes
 */
export function ProjectCodeTable() {
  const { tableKey, refreshTable } = useTableRefresh('project-code');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'code',
        sortable: true,
        title: t`Project Code`
      },
      {
        accessor: 'description',
        sortable: false,
        title: t`Description`
      }
    ];
  }, []);

  function rowActions(record: any): RowAction[] {
    return [
      {
        title: t`Edit`,
        onClick: () => {
          notYetImplemented();
        }
      },
      {
        title: t`Delete`,
        color: 'red',
        onClick: () => {
          notYetImplemented();
        }
      }
    ];
  }

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.project_code_list)}
      tableKey={tableKey}
      columns={columns}
      props={{
        rowActions: rowActions
      }}
    />
  );
}
