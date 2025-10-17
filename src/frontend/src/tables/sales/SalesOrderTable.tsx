import { t } from '@lingui/core/macro';
import { useMemo } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import { ProgressBar } from '@lib/components/ProgressBar';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import { useSalesOrderFields } from '../../forms/SalesOrderForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  CompanyColumn,
  CreatedByColumn,
  CreationDateColumn,
  CurrencyColumn,
  DescriptionColumn,
  LineItemsProgressColumn,
  PercentageColumn,
  ProjectCodeColumn,
  ReferenceColumn,
  ResponsibleColumn,
  ShipmentDateColumn,
  StartDateColumn,
  StatusColumn,
  TargetDateColumn,
  TenantColumn
} from '../ColumnRenderers';
import {
  AssignedToMeFilter,
  CompletedAfterFilter,
  CompletedBeforeFilter,
  CreatedAfterFilter,
  CreatedBeforeFilter,
  CreatedByFilter,
  HasProjectCodeFilter,
  IncludeVariantsFilter,
  MaxDateFilter,
  MinDateFilter,
  OrderStatusFilter,
  OutstandingFilter,
  OverdueFilter,
  ProjectCodeFilter,
  ResponsibleFilter,
  StartDateAfterFilter,
  StartDateBeforeFilter,
  TargetDateAfterFilter,
  TargetDateBeforeFilter,
  TenantFilter
} from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export function SalesOrderTable({
  partId,
  customerId
}: Readonly<{
  partId?: number;
  customerId?: number;
}>) {
  const table = useTable(!!partId ? 'salesorder-part' : 'salesorder-index');
  const user = useUserState();

  const tableFilters: TableFilter[] = useMemo(() => {
    const filters: TableFilter[] = [
      OrderStatusFilter({ model: ModelType.salesorder }),
      OutstandingFilter(),
      OverdueFilter(),
      AssignedToMeFilter(),
      MinDateFilter(),
      MaxDateFilter(),
      CreatedBeforeFilter(),
      CreatedAfterFilter(),
      TargetDateBeforeFilter(),
      TargetDateAfterFilter(),
      StartDateBeforeFilter(),
      StartDateAfterFilter(),
      {
        name: 'has_target_date',
        type: 'boolean',
        label: t`Has Target Date`,
        description: t`Show orders with a target date`
      },
      {
        name: 'has_start_date',
        type: 'boolean',
        label: t`Has Start Date`,
        description: t`Show orders with a start date`
      },
      CompletedBeforeFilter(),
      CompletedAfterFilter(),
      HasProjectCodeFilter(),
      ProjectCodeFilter(),
      TenantFilter(),
      ResponsibleFilter(),
      CreatedByFilter()
    ];

    if (!!partId) {
      filters.push(IncludeVariantsFilter());
    }

    return filters;
  }, [partId]);

  const salesOrderFields = useSalesOrderFields({});

  const newSalesOrder = useCreateApiFormModal({
    url: ApiEndpoints.sales_order_list,
    title: t`Add Sales Order`,
    fields: salesOrderFields,
    initialData: {
      customer: customerId
    },
    follow: true,
    modelType: ModelType.salesorder
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-sales-order'
        tooltip={t`Add Sales Order`}
        onClick={() => newSalesOrder.open()}
        hidden={!user.hasAddRole(UserRoles.sales_order)}
      />
    ];
  }, [user]);

  const tableColumns = useMemo(() => {
    return [
      ReferenceColumn({}),
      {
        accessor: 'customer__name',
        title: t`Customer`,
        sortable: true,
        render: (record: any) => (
          <CompanyColumn company={record.customer_detail} />
        )
      },
      {
        accessor: 'customer_reference',
        title: t`Customer Reference`
      },
      DescriptionColumn({}),
      LineItemsProgressColumn({}),
      {
        accessor: 'shipments_count',
        title: t`Shipments`,
        minWidth: 125,
        render: (record: any) => (
          <ProgressBar
            progressLabel
            value={record.completed_shipments_count}
            maximum={record.shipments_count}
          />
        )
      },
      StatusColumn({ model: ModelType.salesorder }),
      ProjectCodeColumn({
        defaultVisible: false
      }),
      TenantColumn({
        defaultVisible: false
      }),
      CreationDateColumn({
        defaultVisible: false
      }),
      CreatedByColumn({
        defaultVisible: false
      }),
      StartDateColumn({
        defaultVisible: false
      }),
      TargetDateColumn({}),
      ShipmentDateColumn({}),
      ResponsibleColumn({}),
      CurrencyColumn({
        accessor: 'total_price',
        title: t`Total Price`
      }),
      CurrencyColumn({
        accessor: 'subtotal',
        title: t`Subtotal`
      }),
      CurrencyColumn({
        accessor: 'tax_amount',
        title: t`Tax Amount`
      }),
      CurrencyColumn({
        accessor: 'total_with_tax',
        title: t`Total with Tax`
      }),
      PercentageColumn({
        accessor: 'tax_rate',
        title: t`Tax Rate`,
        sortable: true
      })
    ];
  }, []);

  return (
    <>
      {newSalesOrder.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.sales_order_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            customer_detail: true,
            part: partId,
            customer: customerId
          },
          tableFilters: tableFilters,
          tableActions: tableActions,
          modelType: ModelType.salesorder,
          enableSelection: true,
          enableDownload: true,
          enableReports: true
        }}
      />
    </>
  );
}
