import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { renderDate } from '../../../defaults/formatters';
import { ApiPaths } from '../../../enums/ApiEndpoints';
import { ModelType } from '../../../enums/ModelType';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { ThumbnailHoverCard } from '../../images/Thumbnail';
import { ProgressBar } from '../../items/ProgressBar';
import { RenderUser } from '../../render/User';
import { TableColumn } from '../Column';
import {
  CreationDateColumn,
  ProjectCodeColumn,
  ResponsibleColumn,
  StatusColumn,
  TargetDateColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Construct a list of columns for the build order table
 */
function buildOrderTableColumns(): TableColumn[] {
  return [
    {
      accessor: 'reference',
      sortable: true,
      switchable: false,
      title: t`Reference`
    },
    {
      accessor: 'part',
      sortable: true,
      switchable: false,
      title: t`Part`,
      render: (record: any) => {
        let part = record.part_detail;
        return (
          part && (
            <ThumbnailHoverCard
              src={part.thumbnail || part.image}
              text={part.full_name}
              alt={part.description}
              link=""
            />
          )
        );
      }
    },
    {
      accessor: 'title',
      sortable: false,
      title: t`Description`
    },
    {
      accessor: 'completed',
      sortable: true,
      switchable: false,
      title: t`Progress`,
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
      title: t`Priority`,
      sortable: true
    },
    CreationDateColumn(),
    TargetDateColumn(),
    {
      accessor: 'completion_date',
      sortable: true,
      title: t`Completed`,
      render: (record: any) => renderDate(record.completion_date)
    },
    {
      accessor: 'issued_by',
      sortable: true,
      title: t`Issued By`,
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

  const tableFilters = useMemo(() => {
    return [
      {
        // TODO: Filter by status code
        name: 'active',
        type: 'boolean',
        label: t`Active`,
        description: t`Filter by active status`
      },
      {
        name: 'overdue',
        type: 'boolean',
        label: t`Overdue`,
        description: t`Filter by overdue status`
      },
      {
        name: 'assigned_to_me',
        type: 'boolean',
        label: t`Assigned to me`,
        description: t`Filter orders assigned to me`
      }
      // TODO: 'assigned to' filter
      // TODO: 'issued by' filter
      // TODO: 'has project code' filter (see table_filters.js)
      // TODO: 'project code' filter (see table_filters.js)
    ];
  }, []);

  const navigate = useNavigate();

  const table = useTable('buildorder');

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.build_order_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        enableDownload: true,
        params: {
          ...params,
          part_detail: true
        },
        customFilters: tableFilters,
        onRowClick: (row) => navigate(`/build/${row.pk}`)
      }}
    />
  );
}
