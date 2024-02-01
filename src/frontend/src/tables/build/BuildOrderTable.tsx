import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { PartHoverCard } from '../../components/images/Thumbnail';
import { ProgressBar } from '../../components/items/ProgressBar';
import { RenderUser } from '../../components/render/User';
import { renderDate } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { getDetailUrl } from '../../functions/urls';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { TableColumn } from '../Column';
import {
  CreationDateColumn,
  ProjectCodeColumn,
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
    {
      accessor: 'reference',
      sortable: true,
      switchable: false
    },
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
export function BuildOrderTable({ params = {} }: { params?: any }) {
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
        label: t`Status`,
        description: t`Filter by order status`,
        choiceFunction: StatusFilterOptions(ModelType.build)
      },
      {
        name: 'overdue',
        type: 'boolean',
        label: t`Overdue`,
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

  const table = useTable('buildorder');

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.build_order_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        enableDownload: true,
        params: {
          ...params,
          part_detail: true
        },
        tableFilters: tableFilters,
        onRowClick: (row) => navigate(getDetailUrl(ModelType.build, row.pk))
      }}
    />
  );
}
