import { t } from '@lingui/macro';
import { Progress } from '@mantine/core';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ThumbnailHoverCard } from '../../items/Thumbnail';
import { TableColumn } from '../Column';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Construct a list of columns for the build order table
 */
function buildOrderTableColumns(): TableColumn[] {
  return [
    {
      accessor: 'reference',
      sortable: true,
      title: t`Reference`
      // TODO: Link to the build order detail page
    },
    {
      accessor: 'part',
      sortable: true,
      title: t`Part`,
      render: (record: any) => {
        let part = record.part_detail;
        return (
          part && (
            <ThumbnailHoverCard
              src={part.thumbnail || part.image}
              text={part.full_name}
              link=""
            />
          )
        );
      }
    },
    {
      accessor: 'title',
      sortable: false,
      title: t`Description`,
      switchable: true
    },
    {
      accessor: 'project_code',
      title: t`Project Code`,
      sortable: true,
      switchable: false,
      hidden: true
      // TODO: Hide this if project code is not enabled
      // TODO: Custom render function here
    },
    {
      accessor: 'quantity',
      sortable: true,
      title: t`Quantity`,
      switchable: true
    },
    {
      accessor: 'completed',
      sortable: true,
      title: t`Completed`,
      render: (record: any) => {
        let progress =
          record.quantity <= 0 ? 0 : (100 * record.completed) / record.quantity;
        return (
          <Progress
            value={progress}
            label={record.completed}
            color={progress < 100 ? 'blue' : 'green'}
            size="xl"
            radius="xl"
          />
        );
      }
    },
    {
      accessor: 'status',
      sortable: true,
      title: t`Status`,
      switchable: true
      // TODO: Custom render function here (status label)
    },
    {
      accessor: 'priority',
      title: t`Priority`,
      sortable: true,
      switchable: true
    },
    {
      accessor: 'creation_date',
      sortable: true,
      title: t`Created`,
      switchable: true
    },
    {
      accessor: 'target_date',
      sortable: true,
      title: t`Target Date`,
      switchable: true
    },
    {
      accessor: 'completion_date',
      sortable: true,
      title: t`Completed`,
      switchable: true
    },
    {
      accessor: 'issued_by',
      sortable: true,
      title: t`Issued By`,
      switchable: true
      // TODO: custom render function
    },
    {
      accessor: 'responsible',
      sortable: true,
      title: t`Responsible`,
      switchable: true
      // TODO: custom render function
    }
  ];
}

function buildOrderTableFilters(): TableFilter[] {
  return [];
}

function buildOrderTableParams(params: any): any {
  return {
    ...params,
    part_detail: true
  };
}

/*
 * Construct a table of build orders, according to the provided parameters
 */
export function BuildOrderTable({ params = {} }: { params?: any }) {
  // Add required query parameters
  const tableParams = useMemo(() => buildOrderTableParams(params), [params]);
  const tableColumns = useMemo(() => buildOrderTableColumns(), []);
  const tableFilters = useMemo(() => buildOrderTableFilters(), []);

  const navigate = useNavigate();

  tableParams.part_detail = true;

  return (
    <InvenTreeTable
      url="build/"
      enableDownload
      tableKey="build-order-table"
      params={tableParams}
      columns={tableColumns}
      customFilters={tableFilters}
      onRowClick={(row) => navigate(`/build/${row.pk}`)}
    />
  );
}
