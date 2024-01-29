import { t } from '@lingui/macro';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { ModelType } from '../../../enums/ModelType';
import { UserRoles } from '../../../enums/Roles';
import { notYetImplemented } from '../../../functions/notifications';
import { getDetailUrl } from '../../../functions/urls';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { AddItemButton } from '../../buttons/AddItemButton';
import { Thumbnail } from '../../images/Thumbnail';
import {
  CreationDateColumn,
  DescriptionColumn,
  LineItemsProgressColumn,
  ProjectCodeColumn,
  ShipmentDateColumn,
  StatusColumn,
  TargetDateColumn,
  TotalPriceColumn
} from '../ColumnRenderers';
import {
  AssignedToMeFilter,
  OutstandingFilter,
  OverdueFilter,
  StatusFilterOptions,
  TableFilter
} from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export function SalesOrderTable({ params }: { params?: any }) {
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

  // TODO: Row actions

  // TODO: Table actions (e.g. create new sales order)

  const tableColumns = useMemo(() => {
    return [
      {
        accessor: 'reference',
        title: t`Sales Order`,
        sortable: true,
        switchable: false
        // TODO: Display extra information if order is overdue
      },
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
      TotalPriceColumn()
    ];
  }, []);

  const addSalesOrder = useCallback(() => {
    notYetImplemented();
  }, []);

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        tooltip={t`Add Sales Order`}
        onClick={addSalesOrder}
        hidden={!user.hasAddRole(UserRoles.sales_order)}
      />
    ];
  }, [user]);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.sales_order_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          ...params,
          customer_detail: true
        },
        tableFilters: tableFilters,
        tableActions: tableActions,
        onRowClick: (row: any) => {
          if (row.pk) {
            navigate(getDetailUrl(ModelType.salesorder, row.pk));
          }
        }
      }}
    />
  );
}
