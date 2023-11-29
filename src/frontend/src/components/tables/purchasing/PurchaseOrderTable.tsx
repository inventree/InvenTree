import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { ModelType } from '../../../enums/ModelType';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';
import {
  CreationDateColumn,
  DescriptionColumn,
  LineItemsProgressColumn,
  ProjectCodeColumn,
  ResponsibleColumn,
  StatusColumn,
  TargetDateColumn,
  TotalPriceColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Display a table of purchase orders
 */
export function PurchaseOrderTable({ params }: { params?: any }) {
  const navigate = useNavigate();

  const table = useTable('purchase-order');

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
        // TODO: Display extra information if order is overdue
      },
      DescriptionColumn(),
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
      LineItemsProgressColumn(),
      StatusColumn(ModelType.purchaseorder),
      ProjectCodeColumn(),
      CreationDateColumn(),
      TargetDateColumn(),
      TotalPriceColumn(),
      ResponsibleColumn()
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.purchase_order_list)}
      tableState={table}
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
