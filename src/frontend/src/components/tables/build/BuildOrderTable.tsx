import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { renderDate } from '../../../defaults/formatters';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { ThumbnailHoverCard } from '../../images/Thumbnail';
import { ProgressBar } from '../../items/ProgressBar';
import { ModelType } from '../../render/ModelType';
import { RenderOwner, RenderUser } from '../../render/User';
import { TableStatusRenderer } from '../../renderers/StatusRenderer';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';

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
    {
      accessor: 'status',
      sortable: true,
      title: t`Status`,

      render: TableStatusRenderer(ModelType.build)
    },
    {
      accessor: 'project_code',
      title: t`Project Code`,
      sortable: true,
      // TODO: Hide this if project code is not enabled
      render: (record: any) => {
        let project = record.project_code_detail;

        return project ? (
          <TableHoverCard
            value={project.code}
            title={t`Project Code`}
            extra={<Text>{project.description}</Text>}
          />
        ) : (
          '-'
        );
      }
    },
    {
      accessor: 'priority',
      title: t`Priority`,
      sortable: true
    },
    {
      accessor: 'creation_date',
      sortable: true,
      title: t`Created`,
      render: (record: any) => renderDate(record.creation_date)
    },
    {
      accessor: 'target_date',
      sortable: true,
      title: t`Target Date`,
      render: (record: any) => renderDate(record.target_date)
    },
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
    {
      accessor: 'responsible',
      sortable: true,
      title: t`Responsible`,
      render: (record: any) => (
        <RenderOwner instance={record?.responsible_detail} />
      )
    }
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
        label: t`Active`
      },
      {
        name: 'overdue',
        type: 'boolean',
        label: t`Overdue`
      },
      {
        name: 'assigned_to_me',
        type: 'boolean',
        label: t`Assigned to me`
      }
      // TODO: 'assigned to' filter
      // TODO: 'issued by' filter
      // TODO: 'has project code' filter (see table_filters.js)
      // TODO: 'project code' filter (see table_filters.js)
    ];
  }, []);

  const navigate = useNavigate();

  const { tableKey, refreshTable } = useTableRefresh('buildorder');

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.build_order_list)}
      tableKey={tableKey}
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
