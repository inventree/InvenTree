import { t } from '@lingui/core/macro';
import { Group, Text } from '@mantine/core';
import type { DataTableRowExpansionProps } from 'mantine-datatable';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableColumn } from '@lib/types/Tables';
import { ProgressBar } from '../../components/items/ProgressBar';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  DescriptionColumn,
  PartColumn,
  ProjectCodeColumn,
  StatusColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowViewAction } from '../RowActions';
import RowExpansionIcon from '../RowExpansionIcon';
import { BuildLineSubTable } from '../build/BuildLineTable';

/**
 * A "simplified" BuildOrderLineItem table showing all outstanding build order allocations for a given part.
 */
export default function PartBuildAllocationsTable({
  partId
}: Readonly<{
  partId: number;
}>) {
  const user = useUserState();
  const navigate = useNavigate();
  const table = useTable('part-build-allocations');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'build',
        title: t`Build Order`,
        sortable: true,
        switchable: false,
        render: (record: any) => (
          <Group wrap='nowrap' gap='xs'>
            <RowExpansionIcon
              enabled={record.allocated > 0}
              expanded={table.isRowExpanded(record.pk)}
            />
            <Text>{record.build_detail?.reference}</Text>
          </Group>
        )
      },
      {
        accessor: 'part',
        title: t`Assembly`,
        render: (record: any) => <PartColumn part={record.part_detail} />
      },
      DescriptionColumn({
        accessor: 'build_detail.title'
      }),
      ProjectCodeColumn({
        accessor: 'build_detail.project_code_detail'
      }),
      StatusColumn({
        accessor: 'build_detail.status',
        model: ModelType.build,
        title: t`Order Status`,
        switchable: false
      }),
      {
        accessor: 'allocated',
        sortable: true,
        switchable: false,
        title: t`Required Stock`,
        render: (record: any) => (
          <ProgressBar
            progressLabel
            value={record.allocated}
            maximum={record.quantity}
          />
        )
      }
    ];
  }, [table.isRowExpanded]);

  const rowActions = useCallback(
    (record: any) => {
      return [
        RowViewAction({
          title: t`View Build Order`,
          modelType: ModelType.build,
          modelId: record.build,
          hidden: !user.hasViewRole(UserRoles.build),
          navigate: navigate
        })
      ];
    },
    [user]
  );

  // Control row expansion
  const rowExpansion: DataTableRowExpansionProps<any> = useMemo(() => {
    return {
      allowMultiple: true,
      expandable: ({ record }: { record: any }) => {
        // Only items with allocated stock can be expanded
        return table.isRowExpanded(record.pk) || record.allocated > 0;
      },
      content: ({ record }: { record: any }) => {
        return <BuildLineSubTable lineItem={record} />;
      }
    };
  }, [table.isRowExpanded]);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.build_line_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        minHeight: 200,
        params: {
          part: partId,
          consumable: false,
          build_detail: true,
          order_outstanding: true
        },
        enableColumnSwitching: true,
        enableSearch: false,
        rowActions: rowActions,
        rowExpansion: rowExpansion
      }}
    />
  );
}
