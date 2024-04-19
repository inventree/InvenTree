import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { Thumbnail } from '../../components/images/Thumbnail';
import { formatCurrency } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useSalesOrderFields } from '../../forms/SalesOrderForms';
import { getDetailUrl } from '../../functions/urls';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import {
  CreationDateColumn,
  DescriptionColumn,
  LineItemsProgressColumn,
  ProjectCodeColumn,
  ReferenceColumn,
  ShipmentDateColumn,
  StatusColumn,
  TargetDateColumn
} from '../ColumnRenderers';
import {
  AssignedToMeFilter,
  OutstandingFilter,
  OverdueFilter,
  StatusFilterOptions,
  TableFilter
} from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export function SalesOrderTable({
  partId,
  customerId
}: {
  partId?: number;
  customerId?: number;
}) {
  const table = useTable('sales-order');
  const user = useUserState();

  const navigate = useNavigate();

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'status',
        label: t`Status`,
        description: t`Filter by order status`,
        choiceFunction: StatusFilterOptions(ModelType.salesorder)
      },
      OutstandingFilter(),
      OverdueFilter(),
      AssignedToMeFilter()
      // TODO: has_project_code
      // TODO: project_code
    ];
  }, []);

  const salesOrderFields = useSalesOrderFields();

  const newSalesOrder = useCreateApiFormModal({
    url: ApiEndpoints.sales_order_list,
    title: t`Add Sales Order`,
    fields: salesOrderFields,
    initialData: {
      customer: customerId
    },
    onFormSuccess: (response) => {
      if (response.pk) {
        navigate(getDetailUrl(ModelType.salesorder, response.pk));
      } else {
        table.refreshTable();
      }
    }
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        tooltip={t`Add Sales Order`}
        onClick={() => newSalesOrder.open()}
        hidden={!user.hasAddRole(UserRoles.sales_order)}
      />
    ];
  }, [user]);

  const tableColumns = useMemo(() => {
    return [
      ReferenceColumn(),
      {
        accessor: 'customer__name',
        title: t`Customer`,
        sortable: true,
        render: function (record: any) {
          let customer = record.customer_detail ?? {};

          return (
            <Thumbnail
              src={customer?.image}
              alt={customer.name}
              text={customer.name}
            />
          );
        }
      },
      {
        accessor: 'customer_reference',
        title: t`Customer Reference`
      },
      DescriptionColumn({}),
      LineItemsProgressColumn(),
      StatusColumn(ModelType.salesorder),
      ProjectCodeColumn(),
      CreationDateColumn(),
      TargetDateColumn(),
      ShipmentDateColumn(),
      {
        accessor: 'total_price',
        title: t`Total Price`,
        sortable: true,
        render: (record: any) => {
          return formatCurrency(record.total_price, {
            currency: record.order_currency ?? record.customer_detail?.currency
          });
        }
      }
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
          modelType: ModelType.salesorder
        }}
      />
    </>
  );
}
