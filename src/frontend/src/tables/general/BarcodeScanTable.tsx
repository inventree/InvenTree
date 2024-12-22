import { t } from '@lingui/macro';
import { IconTrash } from '@tabler/icons-react';
import { useCallback, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import type { BarcodeScanItem } from '../../components/barcodes/BarcodeScanItem';
import { ActionButton } from '../../components/buttons/ActionButton';
import { RenderInstance } from '../../components/render/Instance';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowViewAction } from '../RowActions';

/**
 * A table for showing barcode scan history data on the scan index page
 */
export default function BarcodeScanTable({
  records,
  onItemsSelected,
  onItemsDeleted
}: {
  records: BarcodeScanItem[];
  onItemsSelected: (items: string[]) => void;
  onItemsDeleted: (items: string[]) => void;
}) {
  const navigate = useNavigate();
  const user = useUserState();

  const table = useTable('barcode-scan-results', 'id');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'instance',
        title: t`Item`,
        sortable: false,
        switchable: false,
        render: (record) => {
          if (record.instance) {
            return (
              <RenderInstance model={record.model} instance={record.instance} />
            );
          } else {
            return '-';
          }
        }
      },
      {
        accessor: 'model',
        title: t`Model`,
        sortable: false
      },
      {
        accessor: 'barcode',
        title: t`Barcode`,
        sortable: false
      },
      {
        accessor: 'timestamp',
        title: t`Timestamp`,
        sortable: false,
        render: (record) => {
          return record.timestamp?.toLocaleString();
        }
      }
    ];
  }, []);

  const rowActions = useCallback((record: BarcodeScanItem) => {
    const actions: RowAction[] = [];

    if (record.model && record.pk && record.instance) {
      actions.push(
        RowViewAction({
          title: t`View Item`,
          modelId: record.instance?.pk,
          modelType: record.model,
          navigate: navigate,
          hidden: !user.hasViewPermission(record.model)
        })
      );
    }

    return actions;
  }, []);

  const tableActions = useMemo(() => {
    return [
      <ActionButton
        disabled={!table.hasSelectedRecords}
        icon={<IconTrash />}
        color='red'
        tooltip={t`Delete selected records`}
        onClick={() => {
          onItemsDeleted(table.selectedIds);
          table.clearSelectedRecords();
        }}
      />
    ];
  }, [table.hasSelectedRecords, table.selectedIds]);

  useEffect(() => {
    onItemsSelected(table.selectedIds);
  }, [table.selectedIds]);

  return (
    <>
      <InvenTreeTable
        tableState={table}
        tableData={records}
        columns={tableColumns}
        props={{
          enableFilters: false,
          enableSelection: true,
          enablePagination: false,
          enableSearch: false,
          enableRefresh: false,
          rowActions: rowActions,
          tableActions: tableActions
        }}
      />
    </>
  );
}
