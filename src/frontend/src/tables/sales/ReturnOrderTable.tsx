import { t } from '@lingui/macro';
import { useCallback, useMemo } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { Thumbnail } from '../../components/images/Thumbnail';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { notYetImplemented } from '../../functions/notifications';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import {
  CreationDateColumn,
  DescriptionColumn,
  LineItemsProgressColumn,
  ProjectCodeColumn,
  ReferenceColumn,
  ResponsibleColumn,
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

export function ReturnOrderTable({ params }: { params?: any }) {
  const table = useTable('return-orders');
  const user = useUserState();

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'status',
        label: t`Status`,
        description: t`Filter by order status`,
        choiceFunction: StatusFilterOptions(ModelType.returnorder)
      },
      OutstandingFilter(),
      OverdueFilter(),
      AssignedToMeFilter()
    ];
  }, []);

  // TODO: Row actions

  // TODO: Table actions (e.g. create new return order)

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
        accessor: 'customer_reference'
      },
      DescriptionColumn({}),
      LineItemsProgressColumn(),
      StatusColumn(ModelType.returnorder),
      ProjectCodeColumn(),
      CreationDateColumn(),
      TargetDateColumn(),
      ResponsibleColumn(),
      TotalPriceColumn()
    ];
  }, []);

  const addReturnOrder = useCallback(() => {
    notYetImplemented();
  }, []);

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        tooltip={t`Add Return Order`}
        onClick={addReturnOrder}
        hidden={!user.hasAddRole(UserRoles.sales_order)}
      />
    ];
  }, [user]);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.return_order_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          ...params,
          customer_detail: true
        },
        tableFilters: tableFilters,
        tableActions: tableActions,
        modelType: ModelType.returnorder
      }}
    />
  );
}
