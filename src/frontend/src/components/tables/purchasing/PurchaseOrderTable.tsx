import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';
import { ProgressBar } from '../../items/ProgressBar';
import { ModelType } from '../../render/ModelType';
import { StatusRenderer } from '../../renderers/StatusRenderer';
import { InvenTreeTable } from '../InvenTreeTable';
import { ProjectCodeHoverCard } from '../TableHoverCard';

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
        accessor: 'line_items',
        title: t`Line Items`,
        sortable: true,
        render: (record: any) => (
          <ProgressBar
            progressLabel={true}
            value={record.completed_lines}
            maximum={record.line_items}
          />
        )
      },
      {
        accessor: 'project_code',
        title: t`Project Code`,
        render: (record: any) => (
          <ProjectCodeHoverCard projectCode={record.project_code_detail} />
        )
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
        title: t`Created`
      },
      {
        accessor: 'target_date',
        title: t`Target Date`
      },

      {
        accessor: 'total_price',
        title: t`Total Price`,
        sortable: true
      },
      {
        accessor: 'responsible',
        title: t`Responsible`,
        sortable: true
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
