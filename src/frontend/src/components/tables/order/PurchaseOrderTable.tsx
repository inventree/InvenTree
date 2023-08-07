import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { Link } from 'react-router-dom';

import { TableColumn } from '../Column';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { supplierRender } from './supplierRender';

/**
 * Construct a list of columns for the purchase order table
 */
function purchaseOrderTableColumns(): TableColumn[] {
  return [
    {
      accessor: 'reference',
      sortable: true,
      title: t`Purchase Order`,
      render: (record: any) => {
        return (
          record.pk && (
            <Link to={`/order/purchase-order/${record.pk}`}>
              {record.reference}
            </Link>
          )
        );
      }
    },
    {
      accessor: 'supplier',
      sortable: true,
      title: t`Supplier`,
      switchable: true,
      render: supplierRender()
    },
    {
      accessor: 'supplier_reference',
      sortable: true,
      title: t`Supplier Reference`,
      switchable: true
    },
    {
      accessor: 'description',
      sortable: true,
      title: t`Description`,
      switchable: true
    },
    {
      accessor: 'project_code',
      title: t`Project Code`,
      sortable: true,
      switchable: true
      // TODO: Hide this if project code is not enabled
      // TODO: Custom render function here
    },
    {
      accessor: 'status',
      sortable: true,
      title: t`Status`,
      switchable: true
      // TODO: Custom render function here (status label)
    },
    {
      accessor: 'creation_date',
      sortable: true,
      title: t`Date`,
      switchable: true
    },
    {
      accessor: 'target_date',
      sortable: true,
      title: t`Target Date`,
      switchable: true
    },
    {
      accessor: 'line_items',
      sortable: true,
      title: t`Items`,
      switchable: true
    },
    {
      accessor: 'total_price',
      sortable: true,
      title: t`Total Cost`,
      switchable: true
      // TODO: Custom render function here (currency)
    },
    {
      accessor: 'responsible',
      sortable: true,
      title: t`Responsible`,
      switchable: true
      // TODO: Custom render function here (responsible label)
    }
  ];
}

function purchaseOrderTableFilters(): TableFilter[] {
  return [];
}

function purchaseOrderTableParams(params: any): any {
  return {
    ...params
  };
}

/*
 * Construct a table of purchase orders, according to the provided parameters
 */
export function PurchaseOrderTable({ params = {} }: { params?: any }) {
  // Add required query parameters
  let tableParams = useMemo(() => purchaseOrderTableParams(params), [params]);
  let tableColumns = useMemo(() => purchaseOrderTableColumns(), []);
  let tableFilters = useMemo(() => purchaseOrderTableFilters(), []);

  tableParams.supplier_detail = true;

  return (
    <InvenTreeTable
      url="order/po/"
      enableDownload
      tableKey="purchase-order-table"
      params={tableParams}
      columns={tableColumns}
      customFilters={tableFilters}
    />
  );
}
