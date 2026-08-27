import { AddItemButton } from '@lib/components/AddItemButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { TableFilter } from '@lib/types/Filters';
import { t } from '@lingui/core/macro';
import { useMemo } from 'react';
import { RenderPart } from '../../components/render/Part';
import {
  CompanyColumn,
  CompletionDateColumn,
  CreationDateColumn,
  DescriptionColumn,
  LinkColumn,
  ReferenceColumn,
  ResponsibleColumn,
  StatusColumn,
  TargetDateColumn,
  UserColumn
} from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { useRepairOrderFields } from '../../forms/RepairOrderForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';
import RepairOrderFilters from './RepairOrderFilters';

export function RepairOrderTable({
  customerId
}: Readonly<{
  customerId?: number;
}>) {
  const table = useTable('repairorders-index', {
    initialFilters: [
      {
        name: 'outstanding',
        value: 'true'
      }
    ]
  });

  const user = useUserState();

  const tableFilters: TableFilter[] = useMemo(() => {
    return RepairOrderFilters({ includeDateFilters: true });
  }, []);

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
        accessor: 'part',
        title: t`Part`,
        sortable: true,
        render: (record: any) =>
          record.part_detail ? (
            <RenderPart instance={record.part_detail} />
          ) : null
      },
      DescriptionColumn({}),
      {
        accessor: 'line_items',
        title: t`Line Items`,
        sortable: false,
        render: (record: any) => record.line_items?.length ?? 0
      },
      StatusColumn({ model: ModelType.repairorder }),
      CreationDateColumn({
        defaultVisible: false
      }),
      TargetDateColumn({}),
      CompletionDateColumn({}),
      UserColumn({
        accessor: 'issued_by_detail',
        ordering: 'issued_by',
        filter: 'issued_by',
        title: t`Issued By`,
        defaultVisible: false
      }),
      ResponsibleColumn({}),
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
            customer: customerId,
            customer_detail: true,
            part_detail: true
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
