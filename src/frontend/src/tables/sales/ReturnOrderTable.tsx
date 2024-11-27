import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { Thumbnail } from '../../components/images/Thumbnail';
import { formatCurrency } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useReturnOrderFields } from '../../forms/ReturnOrderForms';
import { useOwnerFilters, useProjectCodeFilters } from '../../hooks/UseFilter';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import {
  CompletionDateColumn,
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
  CompletedAfterFilter,
  CompletedBeforeFilter,
  CreatedAfterFilter,
  CreatedBeforeFilter,
  HasProjectCodeFilter,
  MaxDateFilter,
  MinDateFilter,
  OutstandingFilter,
  OverdueFilter,
  StatusFilterOptions,
  type TableFilter,
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

  const projectCodeFilters = useProjectCodeFilters();
  const responsibleFilters = useOwnerFilters();

  const tableFilters: TableFilter[] = useMemo(() => {
    const filters: TableFilter[] = [
      {
        name: 'status',
        label: t`Status`,
        description: t`Filter by order status`,
        choiceFunction: StatusFilterOptions(ModelType.returnorder)
      },
      OutstandingFilter(),
      OverdueFilter(),
      AssignedToMeFilter(),
      MinDateFilter(),
      MaxDateFilter(),
      CreatedBeforeFilter(),
      CreatedAfterFilter(),
      TargetDateBeforeFilter(),
      TargetDateAfterFilter(),
      CompletedBeforeFilter(),
      CompletedAfterFilter(),
      {
        name: 'project_code',
        label: t`Project Code`,
        description: t`Filter by project code`,
        choices: projectCodeFilters.choices
      },
      HasProjectCodeFilter(),
      {
        name: 'assigned_to',
        label: t`Responsible`,
        description: t`Filter by responsible owner`,
        choices: responsibleFilters.choices
      }
    ];

    if (!!partId) {
      filters.push({
        name: 'include_variants',
        type: 'boolean',
        label: t`Include Variants`,
        description: t`Include orders for part variants`
      });
    }

    return filters;
  }, [partId, projectCodeFilters.choices, responsibleFilters.choices]);

  const tableColumns = useMemo(() => {
    return [
      ReferenceColumn({}),
      {
        accessor: 'customer__name',
        title: t`Customer`,
        sortable: true,
        render: (record: any) => {
          const customer = record.customer_detail ?? {};

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
      CompletionDateColumn({
        accessor: 'complete_date'
      }),
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
