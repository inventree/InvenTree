import { t } from '@lingui/macro';
import { IconTrash } from '@tabler/icons-react';
import { useEffect, useMemo } from 'react';
import type { BarcodeScanItem } from '../../components/barcodes/BarcodeScanItem';
import { ActionButton } from '../../components/buttons/ActionButton';
import { RenderInstance } from '../../components/render/Instance';
import { useTable } from '../../hooks/UseTable';
import type { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * A table for showing barcode scan history data on the scan index page
 */
export default function BarcodeScanTable({
  records,
  onItemsSelected,
  onItemsDeleted
}: {
  records: BarcodeScanItem[];
  onItemsSelected: (items: BarcodeScanItem[]) => void;
  onItemsDeleted: (items: BarcodeScanItem[]) => void;
}) {
  const table = useTable('barcode-scan-results');

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

  const tableActions = useMemo(() => {
    return [
      <ActionButton
        disabled={!table.hasSelectedRecords}
        icon={<IconTrash />}
        color='red'
        tooltip={t`Delete selected records`}
        onClick={() => {
          onItemsDeleted(table.selectedRecords);
          table.clearSelectedRecords();
        }}
      />
    ];
  }, [table.hasSelectedRecords, table.selectedRecords]);

  useEffect(() => {
    onItemsSelected(table.selectedRecords);
  }, [table.selectedRecords]);

  return (
    <>
      <InvenTreeTable
        tableState={table}
        tableData={records}
        columns={tableColumns}
        props={{
          idAccessor: 'id',
          enableFilters: false,
          enableSelection: true,
          enablePagination: false,
          enableSearch: false,
          enableRefresh: false,
          tableActions: tableActions
        }}
      />
    </>
  );
}
