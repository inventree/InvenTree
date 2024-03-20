import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { PartHoverCard } from '../../components/images/Thumbnail';
import { ProgressBar } from '../../components/items/ProgressBar';
import { RenderUser } from '../../components/render/User';
import { renderDate } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { buildOrderFields } from '../../forms/BuildForms';
import { getDetailUrl } from '../../functions/urls';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import {
  CreationDateColumn,
  ProjectCodeColumn,
  ReferenceColumn,
  ResponsibleColumn,
  StatusColumn,
  TargetDateColumn
} from '../ColumnRenderers';
import { StatusFilterOptions, TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Construct a list of columns for the build order table
 */
function buildOrderTableColumns(): TableColumn[] {
  return [
    ReferenceColumn(),
    {
      accessor: 'part',
      sortable: true,
      switchable: false,
      render: (record: any) => <PartHoverCard part={record.part_detail} />
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
    StatusColumn(ModelType.build),
    ProjectCodeColumn(),
    {
      accessor: 'priority',
      sortable: true
    },
    CreationDateColumn(),
    TargetDateColumn(),
    {
      accessor: 'completion_date',
      sortable: true,
      render: (record: any) => renderDate(record.completion_date)
    },
    {
      accessor: 'issued_by',
      sortable: true,
      render: (record: any) => (
        <RenderUser instance={record?.issued_by_detail} />
      )
    },
    ResponsibleColumn()
  ];
}

/*
 * Construct a table of build orders, according to the provided parameters
 */
export function BuildOrderTable({
  partId,
  parentBuildId,
  salesOrderId
}: {
  partId?: number;
  parentBuildId?: number;
  salesOrderId?: number;
}) {
  const tableColumns = useMemo(() => buildOrderTableColumns(), []);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'active',
        type: 'boolean',
        label: t`Active`,
        description: t`Show active orders`
      },
      {
        name: 'status',
        description: t`Filter by order status`,
        choiceFunction: StatusFilterOptions(ModelType.build)
      },
      {
        name: 'overdue',
        type: 'boolean',
        description: t`Show overdue status`
      },
      {
        name: 'assigned_to_me',
        type: 'boolean',
        label: t`Assigned to me`,
        description: t`Show orders assigned to me`
      }
      // TODO: 'assigned to' filter
      // TODO: 'issued by' filter
      // {
      //   name: 'has_project_code',
      //   title: t`Has Project Code`,
      //   description: t`Show orders with project code`,
      // }
      // TODO: 'has project code' filter (see table_filters.js)
      // TODO: 'project code' filter (see table_filters.js)
    ];
  }, []);

  const navigate = useNavigate();
  const user = useUserState();

  const table = useTable('buildorder');

  const newBuild = useCreateApiFormModal({
    url: ApiEndpoints.build_order_list,
    title: t`Add Build Order`,
    fields: buildOrderFields(),
    initialData: {
      part: partId,
      sales_order: salesOrderId,
      parent: parentBuildId
    },
    onFormSuccess: (data: any) => {
      if (data.pk) {
        navigate(getDetailUrl(ModelType.build, data.pk));
      }
    }
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        hidden={!user.hasAddRole(UserRoles.build)}
        tooltip={t`Add Build Order`}
        onClick={() => newBuild.open()}
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
          enableDownload: true,
          params: {
            part: partId,
            sales_order: salesOrderId,
            parent: parentBuildId,
            part_detail: true
          },
          tableActions: tableActions,
          tableFilters: tableFilters,
          modelType: ModelType.build
        }}
      />
    </>
  );
}
