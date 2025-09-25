import { t } from '@lingui/core/macro';
import { useMemo } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import { formatCurrency } from '../../defaults/formatters';
import { usePurchaseOrderFields } from '../../forms/PurchaseOrderForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  CompanyColumn,
  CompletionDateColumn,
  CreatedByColumn,
  CreationDateColumn,
  DescriptionColumn,
  LineItemsProgressColumn,
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

/**
 * Display a table of purchase orders
 */
export function PurchaseOrderTable({
  supplierId,
  supplierPartId,
  externalBuildId
}: Readonly<{
  supplierId?: number;
  supplierPartId?: number;
  externalBuildId?: number;
}>) {
  const table = useTable('purchase-order');
  const user = useUserState();

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      OrderStatusFilter({ model: ModelType.purchaseorder }),
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
      ProjectCodeFilter(),
      HasProjectCodeFilter(),
      ResponsibleFilter(),
      CreatedByFilter()
    ];
  }, []);

  const tableColumns = useMemo(() => {
    return [
      ReferenceColumn({
        switchable: false
      }),
      DescriptionColumn({}),
      {
        accessor: 'supplier__name',
        title: t`Supplier`,
        sortable: true,
        render: (record: any) => (
          <CompanyColumn company={record.supplier_detail} />
        )
      },
      {
        accessor: 'supplier_reference'
      },
      LineItemsProgressColumn({}),
      StatusColumn({ model: ModelType.purchaseorder }),
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
      {
        accessor: 'total_price',
        title: t`Total Price`,
        sortable: true,
        render: (record: any) => {
          return formatCurrency(record.total_price, {
            currency: record.order_currency || record.supplier_detail?.currency
          });
        }
      },
      ResponsibleColumn({})
    ];
  }, []);

  const purchaseOrderFields = usePurchaseOrderFields({});

  const newPurchaseOrder = useCreateApiFormModal({
    url: ApiEndpoints.purchase_order_list,
    title: t`Add Purchase Order`,
    fields: purchaseOrderFields,
    initialData: {
      supplier: supplierId
    },
    follow: true,
    modelType: ModelType.purchaseorder
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-purchase-order'
        tooltip={t`Add Purchase Order`}
        onClick={() => newPurchaseOrder.open()}
        hidden={!user.hasAddRole(UserRoles.purchase_order)}
      />
    ];
  }, [user]);

  return (
    <>
      {newPurchaseOrder.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.purchase_order_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            supplier_detail: true,
            supplier: supplierId,
            supplier_part: supplierPartId,
            external_build: externalBuildId
          },
          tableFilters: tableFilters,
          tableActions: tableActions,
          modelType: ModelType.purchaseorder,
          enableSelection: true,
          enableDownload: true,
          enableReports: true
        }}
      />
    </>
  );
}
