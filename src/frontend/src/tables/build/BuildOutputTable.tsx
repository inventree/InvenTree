import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { TableColumn } from '../Column';
import { PartColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

export default function BuildOutputTable({
  buildId,
  partId
}: {
  buildId: number;
  partId: number;
}) {
  const table = useTable('build-outputs');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        sortable: true,
        render: (record: any) => PartColumn(record?.part_detail)
      },
      {
        accessor: 'quantity',
        ordering: 'stock',
        sortable: true,
        switchable: false,
        title: t`Build Output`,
        render: (record: any) => {
          // TODO: Implement this!
          return '-';
        }
      },
      {
        accessor: 'allocations',
        sortable: false,
        switchable: false,
        title: t`Allocated Items`,
        render: (record: any) => {
          // TODO: Implement this!
          return '-';
        }
      },
      {
        accessor: 'tests',
        sortable: false,
        switchable: false,
        title: t`Required Tests`,
        render: (record: any) => {
          // TODO: Implement this!
          return '-';
        }
      }
    ];
  }, [buildId, partId]);

  return (
    <>
      <InvenTreeTable
        tableState={table}
        url={apiUrl(ApiEndpoints.stock_item_list)}
        columns={tableColumns}
        props={{
          params: {
            part_detail: true,
            tests: true,
            is_building: true,
            build: buildId
          },
          modelType: ModelType.stockitem
        }}
      />
    </>
  );
}
