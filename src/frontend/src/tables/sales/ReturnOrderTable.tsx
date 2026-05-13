import { t } from '@lingui/core/macro';
import { useMemo } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { TableFilter } from '@lib/types/Filters';
import { formatCurrency } from '../../defaults/formatters';
import { useReturnOrderFields } from '../../forms/ReturnOrderForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';
import {
  CompanyColumn,
  CompletionDateColumn,
  CreatedByColumn,
  CreationDateColumn,
  DescriptionColumn,
  LineItemsProgressColumn,
  LinkColumn,
  ProjectCodeColumn,
  ReferenceColumn,
  ResponsibleColumn,
  StartDateColumn,
  StatusColumn,
  TargetDateColumn,
  UpdatedAtColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import ReturnOrderFilters from './ReturnOrderFilters';

export function ReturnOrderTable({
  partId,
  customerId
}: Readonly<{
  partId?: number;
  customerId?: number;
}>) {
  const table = useTable(
    !!partId ? 'returnorders-part' : 'returnorders-index',
    {
      initialFilters: [
        {
          name: 'outstanding',
          value: 'true'
        }
      ]
    }
  );

  const user = useUserState();

  const tableFilters: TableFilter[] = useMemo(() => {
    return ReturnOrderFilters({ partId: partId, includeDateFilters: true });
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
        accessor: 'customer_reference',
        copyable: true
      },
      DescriptionColumn({}),
      LineItemsProgressColumn({}),
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

  const returnOrderFields = useReturnOrderFields({});

  const newReturnOrder = useCreateApiFormModal({
    url: ApiEndpoints.return_order_list,
    title: t`Add Return Order`,
    fields: returnOrderFields,
    initialData: {
      customer: customerId
    },
    follow: true,
    modelType: ModelType.returnorder,
    keepOpenOption: true
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
          enableReports: true,
          enableLabels: true
        }}
      />
    </>
  );
}
