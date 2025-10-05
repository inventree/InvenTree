import { t } from '@lingui/core/macro';
import { useMemo } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import { useReturnOrderFields } from '../../forms/ReturnOrderForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  CompanyColumn,
  CompletionDateColumn,
  CreatedByColumn,
  CreationDateColumn,
  CurrencyColumn,
  DescriptionColumn,
  LineItemsProgressColumn,
  PercentageColumn,
  ProjectCodeColumn,
  ReferenceColumn,
  ResponsibleColumn,
  StartDateColumn,
  StatusColumn,
  TargetDateColumn
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
  TargetDateBeforeFilter
} from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export function ReturnOrderTable({
  partId,
  customerId
}: Readonly<{
  partId?: number;
  customerId?: number;
}>) {
  const table = useTable(!!partId ? 'returnorders-part' : 'returnorders-index');
  const user = useUserState();

  const tableFilters: TableFilter[] = useMemo(() => {
    const filters: TableFilter[] = [
      OrderStatusFilter({ model: ModelType.returnorder }),
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
      ResponsibleFilter(),
      CreatedByFilter()
    ];

    if (!!partId) {
      filters.push(IncludeVariantsFilter());
    }

    return filters;
  }, [partId]);

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
        accessor: 'customer_reference'
      },
      DescriptionColumn({}),
      LineItemsProgressColumn(),
      StatusColumn({ model: ModelType.returnorder }),
      ProjectCodeColumn({
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
      CompletionDateColumn({
        accessor: 'complete_date'
      }),
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

  const returnOrderFields = useReturnOrderFields({});

  const newReturnOrder = useCreateApiFormModal({
    url: ApiEndpoints.return_order_list,
    title: t`Add Return Order`,
    fields: returnOrderFields,
    initialData: {
      customer: customerId
    },
    follow: true,
    modelType: ModelType.returnorder
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-return-order'
        tooltip={t`Add Return Order`}
        onClick={() => newReturnOrder.open()}
        hidden={!user.hasAddRole(UserRoles.return_order)}
      />
    ];
  }, [user]);

  return (
    <>
      {newReturnOrder.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.return_order_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            part: partId,
            customer: customerId,
            customer_detail: true
          },
          tableFilters: tableFilters,
          tableActions: tableActions,
          modelType: ModelType.returnorder,
          enableSelection: true,
          enableDownload: true,
          enableReports: true
        }}
      />
    </>
  );
}
