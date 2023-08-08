import { t } from '@lingui/macro';
import { Anchor } from '@mantine/core';
import { useMemo } from 'react';

import { formatCurrency } from '../../../functions/formatters';
import { renderDate } from '../../../functions/formatters';
import { projectCodeRender } from '../../renderer/projectCodeRender';
import { stockStatusDisplay } from '../../renderer/stockStatusDisplay';
import { supplierRender } from '../../renderer/supplierRender';
import { TableColumn } from '../Column';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

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
            <Anchor href={`/order/purchase-order/${record.pk}`}>
              {record.reference}
            </Anchor>
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
      title: t`Supplier Reference`,
      switchable: true
    },
    {
      accessor: 'description',
      title: t`Description`,
      switchable: true
    },
    {
      accessor: 'project_code',
      title: t`Project Code`,
      sortable: true,
      switchable: true,
      render: projectCodeRender()
    },
    {
      accessor: 'status',
      sortable: true,
      title: t`Status`,
      switchable: true,
      render: (record: any) => {
        return record.status && stockStatusDisplay(record.status);
      }
    },
    {
      accessor: 'creation_date',
      sortable: true,
      title: t`Date`,
      switchable: true,
      render: (record: any) => {
        return renderDate(record.creation_date);
      }
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
      switchable: true,
      render: (record: any) => {
        return record.total_price && formatCurrency(record.total_price);
      }
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
