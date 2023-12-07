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
import { StatusFilterOptions, TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Display a table of purchase orders
 */
export function PurchaseOrderTable({ params }: { params?: any }) {
  const navigate = useNavigate();

  const table = useTable('purchase-order');

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'status',
        label: t`Status`,
        description: t`Filter by order status`,
        choiceFunction: StatusFilterOptions(ModelType.purchaseorder)
      },
      {
        name: 'outstanding',
        label: t`Outstanding`,
        description: t`Show outstanding orders`
      },
      {
        name: 'overdue',
        label: t`Overdue`,
        description: t`Show overdue orders`
      },
      {
        name: 'assigned_to_me',
        label: t`Assigned to me`,
        description: t`Show orders assigned to me`
      }
      // TODO: has_project_code
      // TODO: project_code
    ];
  }, []);

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
        customFilters: tableFilters,
        onRowClick: (row: any) => {
          if (row.pk) {
            navigate(`/purchasing/purchase-order/${row.pk}`);
          }
        }
      }}
    />
  );
}
