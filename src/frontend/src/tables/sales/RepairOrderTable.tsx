import { AddItemButton } from '@lib/components/AddItemButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { TableFilter } from '@lib/types/Filters';
import { t } from '@lingui/core/macro';
import { useMemo } from 'react';
import { useRepairOrderFields } from '../../forms/RepairOrderForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';
import {
  CompanyColumn,
  DescriptionColumn,
  LinkColumn,
  ReferenceColumn,
  StatusColumn,
  StockColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import RepairOrderFilters from './RepairOrderFilters';

export function RepairOrderTable({
  partId,
  customerId
}: Readonly<{
  partId?: number;
  customerId?: number;
}>) {
  const table = useTable(
    !!partId ? 'repairorders-part' : 'repairorders-index',
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
    return RepairOrderFilters({ partId: partId, includeDateFilters: true });
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
      StockColumn({
        accessor: 'asset_detail',
        title: t`Fixed Asset`
      }),
      DescriptionColumn({}),
      StatusColumn({ model: ModelType.repairorder }),
      LinkColumn({})
    ];
  }, []);

  const repairOrderFields = useRepairOrderFields({});

  const newRepairOrder = useCreateApiFormModal({
    url: ApiEndpoints.repair_order_list,
    title: t`Add Repair Order`,
    fields: repairOrderFields,
    initialData: {
      customer: customerId
    },
    follow: true,
    modelType: ModelType.repairorder,
    keepOpenOption: true
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-repair-order'
        tooltip={t`Add Repair Order`}
        onClick={() => newRepairOrder.open()}
        hidden={!user.hasAddRole(UserRoles.repair_order)}
      />
    ];
  }, [user]);

  return (
    <>
      {newRepairOrder.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.repair_order_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            part: partId,
            customer: customerId,
            customer_detail: true,
            asset_detail: true
          },
          tableFilters: tableFilters,
          tableActions: tableActions,
          modelType: ModelType.repairorder,
          enableSelection: true,
          enableDownload: true,
          enableReports: true,
          enableLabels: true
        }}
      />
    </>
  );
}
