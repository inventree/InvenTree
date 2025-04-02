import { t } from '@lingui/core/macro';
import { useMemo } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ProgressBar } from '../../components/items/ProgressBar';
import { RenderUser } from '../../components/render/User';
import { useBuildOrderFields } from '../../forms/BuildForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  CreationDateColumn,
  DateColumn,
  PartColumn,
  ProjectCodeColumn,
  ReferenceColumn,
  ResponsibleColumn,
  StartDateColumn,
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
  IssuedByFilter,
  MaxDateFilter,
  MinDateFilter,
  OrderStatusFilter,
  OutstandingFilter,
  OverdueFilter,
  PartCategoryFilter,
  ProjectCodeFilter,
  ResponsibleFilter,
  StartDateAfterFilter,
  StartDateBeforeFilter,
  TargetDateAfterFilter,
  TargetDateBeforeFilter
} from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

/*
 * Construct a table of build orders, according to the provided parameters
 */
export function BuildOrderTable({
  partId,
  parentBuildId,
  salesOrderId
}: Readonly<{
  partId?: number;
  parentBuildId?: number;
  salesOrderId?: number;
}>) {
  const table = useTable(!!partId ? 'buildorder-part' : 'buildorder-index');

  const tableColumns = useMemo(() => {
    return [
      ReferenceColumn({}),
      {
        accessor: 'part',
        sortable: true,
        switchable: false,
        render: (record: any) => PartColumn({ part: record.part_detail })
      },
      {
        accessor: 'part_detail.IPN',
        sortable: true,
        switchable: true,
        title: t`IPN`
      },
      {
        accessor: 'title',
        sortable: false
      },
      {
        accessor: 'completed',
        sortable: true,
        switchable: false,
        render: (record: any) => (
          <ProgressBar
            progressLabel={true}
            value={record.completed}
            maximum={record.quantity}
          />
        )
      },
      StatusColumn({ model: ModelType.build }),
      ProjectCodeColumn({}),
      {
        accessor: 'level',
        sortable: true,
        switchable: true,
        hidden: !parentBuildId
      },
      {
        accessor: 'priority',
        sortable: true
      },
      CreationDateColumn({}),
      StartDateColumn({}),
      TargetDateColumn({}),
      DateColumn({
        accessor: 'completion_date',
        title: t`Completion Date`,
        sortable: true
      }),
      {
        accessor: 'issued_by',
        sortable: true,
        render: (record: any) => (
          <RenderUser instance={record?.issued_by_detail} />
        )
      },
      ResponsibleColumn({})
    ];
  }, [parentBuildId]);

  const tableFilters: TableFilter[] = useMemo(() => {
    const filters: TableFilter[] = [
      OutstandingFilter(),
      OrderStatusFilter({ model: ModelType.build }),
      OverdueFilter(),
      AssignedToMeFilter(),
      MinDateFilter(),
      MaxDateFilter(),
      CreatedBeforeFilter(),
      CreatedAfterFilter(),
      TargetDateBeforeFilter(),
      TargetDateAfterFilter(),
      StartDateBeforeFilter(),
      StartDateAfterFilter(),
      {
        name: 'has_target_date',
        type: 'boolean',
        label: t`Has Target Date`,
        description: t`Show orders with a target date`
      },
      {
        name: 'has_start_date',
        type: 'boolean',
        label: t`Has Start Date`,
        description: t`Show orders with a start date`
      },
      CompletedBeforeFilter(),
      CompletedAfterFilter(),
      ProjectCodeFilter(),
      HasProjectCodeFilter(),
      IssuedByFilter(),
      ResponsibleFilter(),
      PartCategoryFilter()
    ];

    // If we are filtering on a specific part, we can include the "include variants" filter
    if (!!partId) {
      filters.push({
        name: 'include_variants',
        type: 'boolean',
        label: t`Include Variants`,
        description: t`Include orders for part variants`
      });
    }

    return filters;
  }, [partId]);

  const user = useUserState();

  const buildOrderFields = useBuildOrderFields({ create: true });

  const newBuild = useCreateApiFormModal({
    url: ApiEndpoints.build_order_list,
    title: t`Add Build Order`,
    fields: buildOrderFields,
    initialData: {
      part: partId,
      sales_order: salesOrderId,
      parent: parentBuildId
    },
    follow: true,
    modelType: ModelType.build
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        hidden={!user.hasAddRole(UserRoles.build)}
        tooltip={t`Add Build Order`}
        onClick={() => newBuild.open()}
        key='add-build-order'
      />
    ];
  }, [user]);

  return (
    <>
      {newBuild.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.build_order_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            part: partId,
            ancestor: parentBuildId,
            sales_order: salesOrderId,
            part_detail: true
          },
          tableActions: tableActions,
          tableFilters: tableFilters,
          modelType: ModelType.build,
          enableSelection: true,
          enableReports: true,
          enableDownload: true
        }}
      />
    </>
  );
}
