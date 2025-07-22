import { type RowAction, RowDeleteAction } from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';
import { AttachmentLink } from '../../components/items/AttachmentLink';
import { RenderUser } from '../../components/render/User';
import { useDeleteApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { DateColumn } from '../ColumnRenderers';
import { UserFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export default function ExportSessionTable() {
  const table = useTable('exportsession');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'output',
        sortable: false,
        render: (record: any) => <AttachmentLink attachment={record.output} />
      },
      {
        accessor: 'output_type',
        title: t`Output Type`,
        sortable: true
      },
      {
        accessor: 'plugin',
        title: t`Plugin`,
        sortable: true
      },
      DateColumn({
        accessor: 'created',
        title: t`Exported On`,
        sortable: true
      }),
      {
        accessor: 'user',
        sortable: true,
        title: t`User`,
        render: (record: any) => RenderUser({ instance: record.user_detail })
      }
    ];
  }, []);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [UserFilter({})];
  }, []);

  const [selectedRow, setSeletectedRow] = useState<any>({});

  const deleteRow = useDeleteApiFormModal({
    url: ApiEndpoints.data_output,
    pk: selectedRow.pk,
    title: t`Delete Output`,
    onFormSuccess: () => table.refreshTable()
  });

  const rowActions = useCallback((record: any): RowAction[] => {
    return [
      RowDeleteAction({
        onClick: () => {
          setSeletectedRow(record);
          deleteRow.open();
        }
      })
    ];
  }, []);

  return (
    <>
      {deleteRow.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.data_output)}
        tableState={table}
        columns={columns}
        props={{
          enableBulkDelete: true,
          enableSelection: true,
          enableSearch: false,
          rowActions: rowActions,
          tableFilters: tableFilters
        }}
      />
    </>
  );
}
