import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { PartHoverCard } from '../../images/Thumbnail';
import { TableColumn } from '../Column';
import { BooleanColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export default function BuildLineTable({ params = {} }: { params?: any }) {
  const table = useTable('buildline');
  const user = useUserState();
  const navigate = useNavigate();

  const tableFilters: TableFilter[] = useMemo(() => {
    return [];
  }, []);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'bom_item',
        title: t`Part`,
        sortable: true,
        switchable: false,
        render: (record: any) => <PartHoverCard part={record.part_detail} />
      },
      {
        accessor: 'reference',
        title: t`Reference`,
        render: (record: any) => record.bom_item_detail.reference
      },
      BooleanColumn({
        accessor: 'bom_item_detail.consumable',
        title: t`Consumable`
      }),
      BooleanColumn({
        accessor: 'bom_item_detail.optional',
        title: t`Optional`
      }),
      {
        accessor: 'unit_quantity',
        title: t`Unit Quantity`,
        sortable: true,
        render: (record: any) => record.bom_item_detail.quantity
        // TODO: More information displayed here
      },
      {
        accessor: 'quantity',
        title: t`Required Quantity`,
        sortable: true
        // TODO: More information displayed here
      },
      {
        accessor: 'available_stock',
        title: t`Available`,
        sortable: true
        // TODO: More information displayed here
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
        tableFilters: tableFilters,
        onRowClick: (row: any) => {
          if (row?.part_detail?.pk) {
            navigate(`/part/${row.part_detail.pk}`);
          }
        }
      }}
    />
  );
}
