import { t } from '@lingui/macro';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { Thumbnail } from '../../components/images/Thumbnail';
import { formatCurrency } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useReturnOrderFields } from '../../forms/SalesOrderForms';
import { notYetImplemented } from '../../functions/notifications';
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
  ResponsibleColumn,
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

export function ReturnOrderTable({ params }: { params?: any }) {
  const table = useTable('return-orders');
  const user = useUserState();
  const navigate = useNavigate();

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

  const returnOrderFields = useReturnOrderFields();

  const newReturnOrder = useCreateApiFormModal({
    url: ApiEndpoints.return_order_list,
    title: t`Add Return Order`,
    fields: returnOrderFields,
    onFormSuccess: (response) => {
      if (response.pk) {
        navigate(getDetailUrl(ModelType.returnorder, response.pk));
      } else {
        table.refreshTable();
      }
    }
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
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
            ...params,
            customer_detail: true
          },
          tableFilters: tableFilters,
          tableActions: tableActions,
          modelType: ModelType.returnorder
        }}
      />
    </>
  );
}
