import { t } from '@lingui/core/macro';
import { useMemo } from 'react';

import { ProgressBar } from '@lib/components/ProgressBar';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import {
  CompanyColumn,
  DateColumn,
  ReferenceColumn,
  StatusColumn
} from '../../components/tables/ColumnRenderers';
import {
  IncludeVariantsFilter,
  StatusFilterOptions
} from '../../components/tables/Filter';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { formatCurrency } from '../../defaults/formatters';

export default function PartSalesOrdersTable({
  partId
}: Readonly<{
  partId: number;
}>) {
  const table = useTable('partsalesorders');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      ReferenceColumn({
        accessor: 'order_detail.reference',
        ordering: 'order',
        sortable: true,
        switchable: false,
        filter: ['order_outstanding', 'completed'],
        title: t`Sales Order`
      }),
      StatusColumn({
        accessor: 'order_detail.status',
        sortable: true,
        ordering: 'status',
        title: t`Status`,
        filter: 'order_status',
        model: ModelType.salesorder
      }),
      {
        accessor: 'customer_detail.name',
        title: t`Customer`,
        sortable: false,
        switchable: true,
        render: (record: any) => (
          <CompanyColumn company={record.customer_detail} />
        )
      },
      {
        accessor: 'quantity',
        sortable: true,
        switchable: false,
        render: (record: any) => (
          <ProgressBar
            progressLabel
            value={record.shipped}
            maximum={record.quantity}
          />
        )
      },
      DateColumn({
        accessor: 'target_date',
        title: t`Target Date`
      }),
      DateColumn({
        accessor: 'order_detail.shipment_date',
        ordering: 'shipment_date',
        title: t`Shipment Date`
      }),
      {
        accessor: 'sale_price',
        render: (record: any) =>
          formatCurrency(record.sale_price, {
            currency: record.sale_price_currency
          })
      }
    ];
  }, []);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'order_outstanding',
        label: t`Outstanding`,
        description: t`Show outstanding orders`
      },
      {
        name: 'completed',
        label: t`Completed`,
        description: t`Show completed line items`
      },
      {
        name: 'order_status',
        label: t`Order Status`,
        description: t`Filter by order status`,
        choiceFunction: StatusFilterOptions(ModelType.salesorder)
      },
      IncludeVariantsFilter()
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.sales_order_line_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          part: partId,
          part_detail: true,
          order_detail: true,
          customer_detail: true
        },
        modelField: 'order',
        modelType: ModelType.salesorder,
        tableFilters: tableFilters
      }}
    />
  );
}
