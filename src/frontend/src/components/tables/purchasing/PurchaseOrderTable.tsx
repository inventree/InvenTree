import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { formatCurrency, renderDate } from '../../../defaults/formatters';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';
import { ModelType } from '../../render/ModelType';
import { StatusRenderer } from '../../renderers/StatusRenderer';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Display a table of purchase orders
 */
export function PurchaseOrderTable({ params }: { params?: any }) {
  const navigate = useNavigate();

  const { tableKey } = useTableRefresh('purchase-order');

  // TODO: Custom filters

  // TODO: Row actions

  // TODO: Table actions (e.g. create new purchase order)

  const tableColumns = useMemo(() => {
    return [
      {
        accessor: 'reference',
        title: t`Reference`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'description',
        title: t`Description`
      },
      {
        accessor: 'supplier__name',
        title: t`Supplier`,
        sortable: true,
        render: function (record: any) {
          let supplier = record.supplier_detail ?? {};

          return (
            <Thumbnail
              src={supplier?.image}
              alt={supplier.name}
              text={supplier.name}
            />
          );
        }
      },
      {
        accessor: 'supplier_reference',
        title: t`Supplier Reference`
      },
      {
        accessor: 'project_code',
        title: t`Project Code`

        // TODO: Custom project code formatter
      },
      {
        accessor: 'status',
        title: t`Status`,
        sortable: true,

        render: (record: any) =>
          StatusRenderer({
            status: record.status,
            type: ModelType.purchaseorder
          })
      },
      {
        accessor: 'creation_date',
        title: t`Created`,
        render: (record: any) => renderDate(record.creation_date)
      },
      {
        accessor: 'target_date',
        title: t`Target Date`,
        render: (record: any) => renderDate(record.target_date)
      },
      {
        accessor: 'line_items',
        title: t`Line Items`,
        sortable: true
      },
      {
        accessor: 'total_price',
        sortable: true,
        title: t`Total Price`,
        render: (record: any) =>
          formatCurrency(record.total_price, {
            currency: record.order_currency
          })
      },
      {
        accessor: 'responsible',
        title: t`Responsible`,
        sortable: true

        // TODO: custom 'owner' formatter
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.purchase_order_list)}
      tableKey={tableKey}
      columns={tableColumns}
      props={{
        params: {
          ...params,
          supplier_detail: true
        },
        onRowClick: (row: any) => {
          if (row.pk) {
            navigate(`/purchasing/purchase-order/${row.pk}`);
          }
        }
      }}
    />
  );
}
