import { t } from '@lingui/macro';
import { useMemo } from 'react';
import type { BarcodeScanItem } from '../../components/barcodes/BarcodeScanItem';
import { RenderInstance } from '../../components/render/Instance';
import { useTable } from '../../hooks/UseTable';
import type { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * A table for showing barcode scan history data on the scan index page
 */
export default function BarcodeScanTable({
  records
}: {
  records: BarcodeScanItem[];
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
          enableRefresh: false
        }}
      />
    </>
  );
}
