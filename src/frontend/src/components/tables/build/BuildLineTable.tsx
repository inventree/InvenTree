import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { TableColumn } from '../Column';
import { BooleanColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export default function BuildLineTable({ params = {} }: { params?: any }) {
  const table = useTable('buildline');
  const user = useUserState();

  const tableFilters: TableFilter[] = useMemo(() => {
    return [];
  }, []);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'bom_item',
        title: t`Part`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'reference',
        title: t`Reference`
      },
      BooleanColumn({
        accessor: 'consumable',
        title: t`Consumable`
      }),
      BooleanColumn({
        accessor: 'optional',
        title: t`Optional`
      }),
      {
        accessor: 'unit_quantity',
        title: t`Unit Quantity`
      },
      {
        accessor: 'quantity',
        title: t`Required Quantity`
      },
      {
        accessor: 'available_stock',
        title: t`Available`
      },
      {
        accessor: 'allocated',
        title: t`Allocated`
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.build_line_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          ...params,
          part_detail: true
        },
        tableFilters: tableFilters
      }}
    />
  );
}
