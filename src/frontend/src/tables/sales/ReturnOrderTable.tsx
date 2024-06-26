import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { Thumbnail } from '../../components/images/Thumbnail';
import { formatCurrency } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useReturnOrderFields } from '../../forms/SalesOrderForms';
import { useOwnerFilters, useProjectCodeFilters } from '../../hooks/UseFilter';
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

  const projectCodeFilters = useProjectCodeFilters();
  const responsibleFilters = useOwnerFilters();

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
      AssignedToMeFilter(),
      {
        name: 'project_code',
        label: t`Project Code`,
        description: t`Filter by project code`,
        choices: projectCodeFilters.choices
      },
      {
        name: 'has_project_code',
        label: t`Has Project Code`,
        description: t`Filter by whether the purchase order has a project code`
      },
      {
        name: 'assigned_to',
        label: t`Responsible`,
        description: t`Filter by responsible owner`,
        choices: responsibleFilters.choices
      }
    ];
  }, [projectCodeFilters.choices, responsibleFilters.choices]);

  const tableColumns = useMemo(() => {
    return [
      ReferenceColumn({}),
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
      StatusColumn({ model: ModelType.returnorder }),
      ProjectCodeColumn({}),
      CreationDateColumn({}),
      TargetDateColumn({}),
      ResponsibleColumn({}),
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
    follow: true,
    modelType: ModelType.returnorder
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
          modelType: ModelType.returnorder,
          enableSelection: true,
          enableDownload: true,
          enableReports: true
        }}
      />
    </>
  );
}
