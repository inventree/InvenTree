import { t } from '@lingui/core/macro';
import { Table, Text } from '@mantine/core';
import { type ReactNode, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { formatDecimal } from '@lib/functions/Formatting';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { RenderBuildOrder } from '../../components/render/Build';
import { RenderCompany } from '../../components/render/Company';
import {
  RenderPurchaseOrder,
  RenderReturnOrder,
  RenderSalesOrder
} from '../../components/render/Order';
import { RenderPart } from '../../components/render/Part';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import {
  RenderStockItem,
  RenderStockLocation
} from '../../components/render/Stock';
import { RenderUser } from '../../components/render/User';
import { useTable } from '../../hooks/UseTable';
import {
  DateColumn,
  DescriptionColumn,
  PartColumn,
  StockColumn
} from '../ColumnRenderers';
import {
  IncludeVariantsFilter,
  MaxDateFilter,
  MinDateFilter,
  UserFilter
} from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

type StockTrackingEntry = {
  label: string;
  key: string;
  details: ReactNode;
};

export function StockTrackingTable({
  itemId,
  partId
}: Readonly<{
  itemId?: number;
  partId?: number;
}>) {
  const navigate = useNavigate();
  const table = useTable(partId ? 'part_stock_tracking' : 'stock_tracking');

  // Render "details" for a stock tracking record
  const renderDetails = useCallback(
    (record: any) => {
      const deltas: any = record?.deltas ?? {};

      const entries: StockTrackingEntry[] = [
        {
          label: t`Stock Item`,
          key: 'stockitem',
          details:
            deltas.stockitem_detail &&
            RenderStockItem({ instance: deltas.stockitem_detail, link: true })
        },
        {
          label: t`Stock Item`,
          key: 'item',
          details:
            deltas.item_detail &&
            RenderStockItem({
              instance: deltas.item_detail,
              link: true
            })
        },
        {
          label: t`Status`,
          key: 'status',
          details:
            deltas.status &&
            StatusRenderer({
              status: deltas.status,
              type: ModelType.stockitem,
              fallbackStatus: deltas.status_logical
            })
        },
        {
          label: t`Old Status`,
          key: 'old_status',
          details:
            deltas.old_status &&
            StatusRenderer({
              status: deltas.old_status,
              type: ModelType.stockitem,
              fallbackStatus: deltas.old_status_logical
            })
        },
        {
          label: t`Quantity`,
          key: 'quantity',
          details: formatDecimal(deltas.quantity)
        },
        {
          label: t`Added`,
          key: 'added',
          details: deltas.added
        },
        {
          label: t`Removed`,
          key: 'removed',
          details: deltas.removed
        },
        {
          label: t`Part`,
          key: 'part',
          details:
            deltas.part_detail &&
            RenderPart({
              instance: deltas.part_detail,
              link: true,
              navigate: navigate
            })
        },
        {
          label: t`Location`,
          key: 'location',
          details:
            deltas.location_detail &&
            RenderStockLocation({
              instance: deltas.location_detail,
              link: true,
              navigate: navigate
            })
        },
        {
          label: t`Build Order`,
          key: 'buildorder',
          details:
            deltas.buildorder_detail &&
            RenderBuildOrder({
              instance: deltas.buildorder_detail,
              link: true,
              navigate: navigate
            })
        },
        {
          label: t`Purchase Order`,
          key: 'purchaseorder',
          details:
            deltas.purchaseorder_detail &&
            RenderPurchaseOrder({
              instance: deltas.purchaseorder_detail,
              link: true,
              navigate: navigate
            })
        },
        {
          label: t`Sales Order`,
          key: 'salesorder',
          details:
            deltas.salesorder_detail &&
            RenderSalesOrder({
              instance: deltas.salesorder_detail,
              link: true,
              navigate: navigate
            })
        },
        {
          label: t`Return Order`,
          key: 'returnorder',
          details:
            deltas.returnorder_detail &&
            RenderReturnOrder({
              instance: deltas.returnorder_detail,
              link: true,
              navigate: navigate
            })
        },
        {
          label: t`Customer`,
          key: 'customer',
          details:
            deltas.customer_detail &&
            RenderCompany({
              instance: deltas.customer_detail,
              link: true,
              navigate: navigate
            })
        }
      ];

      return (
        <Table striped>
          <Table.Tbody>
            {entries.map(
              (entry) =>
                entry.details && (
                  <Table.Tr key={entry.key}>
                    <Table.Td>
                      <Text>{entry.label}</Text>
                    </Table.Td>
                    <Table.Td>{entry.details}</Table.Td>
                  </Table.Tr>
                )
            )}
          </Table.Tbody>
        </Table>
      );
    },
    [navigate]
  );

  const filters: TableFilter[] = useMemo(() => {
    return [
      MinDateFilter(),
      MaxDateFilter(),
      IncludeVariantsFilter(),
      UserFilter({
        name: 'user',
        label: t`User`,
        description: t`Filter by user`
      })
    ];
  }, []);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      DateColumn({
        switchable: false
      }),
      PartColumn({
        title: t`Part`,
        part: 'part_detail',
        switchable: true,
        hidden: !partId
      }),
      {
        title: t`IPN`,
        accessor: 'part_detail.IPN',
        sortable: true,
        defaultVisible: false,
        switchable: true,
        hidden: !partId
      },
      StockColumn({
        title: t`Stock Item`,
        accessor: 'item_detail',
        nullMessage: (
          <Text size='sm' c='red'>{t`Stock item no longer exists`}</Text>
        ),
        sortable: false,
        switchable: false,
        hidden: !partId
      }),
      DescriptionColumn({
        accessor: 'label'
      }),
      {
        accessor: 'details',
        title: t`Details`,
        switchable: false,
        render: renderDetails
      },
      {
        accessor: 'notes',
        title: t`Notes`,
        sortable: false,
        switchable: true
      },
      {
        accessor: 'user',
        title: t`User`,
        render: (record: any) => {
          if (!record.user_detail) {
            return <Text size='sm' fs='italic'>{t`No user information`}</Text>;
          }

          return RenderUser({ instance: record.user_detail });
        }
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      tableState={table}
      url={apiUrl(ApiEndpoints.stock_tracking_list)}
      columns={tableColumns}
      props={{
        params: {
          item: itemId,
          part: partId,
          part_detail: partId ? true : undefined,
          item_detail: partId ? true : undefined,
          user_detail: true
        },
        enableDownload: true,
        tableFilters: filters,
        modelType: partId ? ModelType.stockitem : undefined,
        modelField: 'item'
      }}
    />
  );
}
