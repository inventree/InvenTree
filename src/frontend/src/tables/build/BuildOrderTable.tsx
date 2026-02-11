import { t } from '@lingui/core/macro';
import { useMemo } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import { ProgressBar } from '@lib/components/ProgressBar';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import { useBuildOrderFields } from '../../forms/BuildForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import {
  BooleanColumn,
  CreationDateColumn,
  DateColumn,
  DescriptionColumn,
  PartColumn,
  ProjectCodeColumn,
  ReferenceColumn,
  ResponsibleColumn,
  StartDateColumn,
  StatusColumn,
  TargetDateColumn,
  UserColumn
} from '../ColumnRenderers';
import {
  AssignedToMeFilter,
  CompletedAfterFilter,
  CompletedBeforeFilter,
  CreatedAfterFilter,
  CreatedBeforeFilter,
  HasProjectCodeFilter,
  IncludeVariantsFilter,
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
  const globalSettings = useGlobalSettingsState();
  const table = useTable(!!partId ? 'buildorder-part' : 'buildorder-index');

  const tableColumns = useMemo(() => {
    return [
      ReferenceColumn({}),
      PartColumn({
        switchable: false
      }),
      {
        accessor: 'part_detail.IPN',
        sortable: true,
        ordering: 'IPN',
        switchable: true,
        title: t`IPN`
      },
      {
        accessor: 'part_detail.revision',
        title: t`Revision`,
        sortable: true,
        defaultVisible: false
      },
      DescriptionColumn({
        accessor: 'title',
        sortable: false
      }),
      {
        accessor: 'completed',
        title: t`Completed`,
        minWidth: 125,
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
      ProjectCodeColumn({
        defaultVisible: false
      }),
      {
        accessor: 'level',
        sortable: true,
        switchable: true,
        hidden: !parentBuildId,
        defaultVisible: false
      },
      {
        accessor: 'priority',
        sortable: true,
        defaultVisible: false
      },
      BooleanColumn({
        accessor: 'external',
        title: t`External`,
        sortable: true,
        switchable: true,
        hidden: !globalSettings.isSet('BUILDORDER_EXTERNAL_BUILDS')
      }),
      CreationDateColumn({
        defaultVisible: false
      }),
      StartDateColumn({
        defaultVisible: false
      }),
      TargetDateColumn({}),
      DateColumn({
        accessor: 'completion_date',
        title: t`Completion Date`,
        sortable: true
      }),
      UserColumn({
        accessor: 'issued_by_detail',
        ordering: 'issued_by',
        title: t`Issued By`
      }),
      ResponsibleColumn({})
    ];
  }, [parentBuildId, globalSettings]);

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
      {
        name: 'external',
        label: t`External`,
        description: t`Show external build orders`,
        active: globalSettings.isSet('BUILDORDER_EXTERNAL_BUILDS')
      },
      PartCategoryFilter()
    ];

    // If we are filtering on a specific part, we can include the "include variants" filter
    if (!!partId) {
      filters.push(IncludeVariantsFilter());
    }

    return filters;
  }, [partId, globalSettings]);

  const user = useUserState();

  const buildOrderFields = useBuildOrderFields({
    create: true,
    modalId: 'create-build-order'
  });

  const newBuild = useCreateApiFormModal({
    url: ApiEndpoints.build_order_list,
    title: t`Add Build Order`,
    modalId: 'create-build-order',
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
          enableLabels: true,
          enableDownload: true
        }}
      />
    </>
  );
}
