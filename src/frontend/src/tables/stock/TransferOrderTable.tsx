import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { AddItemButton, UserRoles } from '@lib/index';
import type { TableFilter } from '@lib/types/Filters';
import { t } from '@lingui/core/macro';
import { useMemo } from 'react';
import { useTransferOrderFields } from '../../forms/TransferOrderForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  BooleanColumn,
  CompletionDateColumn,
  CreatedByColumn,
  CreationDateColumn,
  DescriptionColumn,
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

export function TransferOrderTable({
  partId
}: Readonly<{
  partId?: number;
}>) {
  const table = useTable(
    !!partId ? 'transferorders-part' : 'transferorders-index'
  );
  const user = useUserState();

  const tableFilters: TableFilter[] = useMemo(() => {
    const filters: TableFilter[] = [
      OrderStatusFilter({ model: ModelType.transferorder }),
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
      DescriptionColumn({}),
      BooleanColumn({
        accessor: 'consume',
        title: t`Consume Stock`,
        sortable: true,
        switchable: true
      }),
      //   LineItemsProgressColumn({}),
      StatusColumn({ model: ModelType.transferorder }),
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
      ResponsibleColumn({})
    ];
  }, []);

  const transferOrderFields = useTransferOrderFields({});

  const newTransferOrder = useCreateApiFormModal({
    url: ApiEndpoints.transfer_order_list,
    title: t`Add Transfer Order`,
    fields: transferOrderFields,
    initialData: {},
    follow: true,
    modelType: ModelType.transferorder
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-transfer-order'
        tooltip={t`Add Transfer Order`}
        onClick={() => newTransferOrder.open()}
        hidden={!user.hasAddRole(UserRoles.transfer_order)}
      />
    ];
  }, [user]);

  return (
    <>
      {newTransferOrder.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.transfer_order_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            part: partId
            // customer: customerId,
            // customer_detail: true
          },
          tableFilters: tableFilters,
          tableActions: tableActions,
          modelType: ModelType.transferorder,
          enableSelection: true,
          enableDownload: true,
          enableReports: true,
          enableLabels: true
        }}
      />
    </>
  );
}
