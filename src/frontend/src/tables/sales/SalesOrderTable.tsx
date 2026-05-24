import { t } from '@lingui/core/macro';
import { useMemo } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import { ProgressBar } from '@lib/components/ProgressBar';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { TableFilter } from '@lib/types/Filters';
import { formatCurrency } from '../../defaults/formatters';
import { useSalesOrderFields } from '../../forms/SalesOrderForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';
import {
  AllocatedLinesProgressColumn,
  CompanyColumn,
  CreatedByColumn,
  CreationDateColumn,
  DescriptionColumn,
  LineItemsProgressColumn,
  LinkColumn,
  ProjectCodeColumn,
  ReferenceColumn,
  ResponsibleColumn,
  ShipmentDateColumn,
  StartDateColumn,
  StatusColumn,
  TargetDateColumn,
  UpdatedAtColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import SalesOrderFilters from './SalesOrderFilters';

export function SalesOrderTable({
  partId,
  customerId
}: Readonly<{
  partId?: number;
  customerId?: number;
}>) {
  const table = useTable(!!partId ? 'salesorder-part' : 'salesorder-index', {
    initialFilters: [
      {
        name: 'outstanding',
        value: 'true'
      }
    ]
  });
  const user = useUserState();

  const tableFilters: TableFilter[] = useMemo(() => {
    return SalesOrderFilters({ partId: partId, includeDateFilters: true });
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
    modelType: ModelType.salesorder,
    keepOpenOption: true
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
        title: t`Customer Reference`,
        copyable: true
      },
      DescriptionColumn({}),
      LineItemsProgressColumn({}),
      AllocatedLinesProgressColumn({
        defaultVisible: false
      }),
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
      UpdatedAtColumn({
        defaultVisible: false
      }),
      ResponsibleColumn({}),
      {
        accessor: 'total_price',
        title: t`Total Price`,
        sortable: true,
        render: (record: any) => {
          return formatCurrency(record.total_price, {
            currency: record.order_currency || record.customer_detail?.currency
          });
        }
      },
      LinkColumn({})
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
          enableReports: true,
          enableLabels: true
        }}
      />
    </>
  );
}
