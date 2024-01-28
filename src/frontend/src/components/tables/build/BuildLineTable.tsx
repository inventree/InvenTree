import { t } from '@lingui/macro';
import {
  IconArrowRight,
  IconShoppingCart,
  IconTool
} from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { PartHoverCard } from '../../images/Thumbnail';
import { ProgressBar } from '../../items/ProgressBar';
import { TableColumn } from '../Column';
import { BooleanColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction } from '../RowActions';

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
        sortable: true,
        switchable: false
        // TODO: More information displayed here
      },
      {
        accessor: 'allocated',
        title: t`Allocated`,
        switchable: false,
        render: (record: any) => {
          return (
            <ProgressBar
              progressLabel={true}
              value={record.allocated}
              maximum={record.quantity}
            />
          );
        }
      }
    ];
  }, []);

  const rowActions: RowAction[] = useCallback(
    (record: any) => {
      let part = record.part_detail;

      // Consumable items have no appropriate actions
      if (record?.bom_item_detail?.consumable) {
        return [];
      }

      return [
        {
          icon: <IconArrowRight />,
          title: t`Allocate Stock`,
          hidden: record.allocated >= record.quantity,
          color: 'green'
        },
        {
          icon: <IconShoppingCart />,
          title: t`Order Stock`,
          hidden: !part?.purchaseable,
          color: 'blue'
        },
        {
          icon: <IconTool />,
          title: t`Build Stock`,
          hidden: !part?.assembly,
          color: 'blue'
        }
      ];
    },
    [user]
  );

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
        rowActions: rowActions,
        onRowClick: (row: any) => {
          if (row?.part_detail?.pk) {
            navigate(`/part/${row.part_detail.pk}`);
          }
        }
      }}
    />
  );
}
