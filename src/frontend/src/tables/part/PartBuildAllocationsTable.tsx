import { t } from '@lingui/core/macro';
import { Group, Text } from '@mantine/core';
import type { DataTableRowExpansionProps } from 'mantine-datatable';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ProgressBar } from '@lib/components/ProgressBar';
import { RowViewAction } from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { IconCircleCheck } from '@tabler/icons-react';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  DescriptionColumn,
  PartColumn,
  ProjectCodeColumn,
  StatusColumn
} from '../ColumnRenderers';
import { IncludeVariantsFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
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
      PartColumn({
        part: 'assembly_detail',
        title: t`Assembly`
      }),
      {
        accessor: 'assembly_detail.IPN',
        title: t`Assembly IPN`
      },
      PartColumn({
        part: 'part_detail',
        defaultVisible: false
      }),
      {
        accessor: 'part_detail.IPN',
        defaultVisible: false,
        title: t`Part IPN`
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
        render: (record: any) => {
          const required = Math.max(0, record.quantity - record.consumed);

          if (required <= 0) {
            return (
              <Group gap='xs' wrap='nowrap'>
                <IconCircleCheck size={14} color='green' />
                <Text size='sm' style={{ fontStyle: 'italic' }}>
                  {record.consumed >= record.quantity
                    ? t`Fully consumed`
                    : t`Fully allocated`}
                </Text>
              </Group>
            );
          }

          return (
            <ProgressBar
              progressLabel
              value={record.allocated}
              maximum={required}
            />
          );
        }
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

  const tableFilters: TableFilter[] = useMemo(() => {
    return [IncludeVariantsFilter()];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.build_line_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        minHeight: 300,
        params: {
          part: partId,
          consumable: false,
          part_detail: false,
          bom_item_detail: false,
          project_code_detail: true,
          assembly_detail: true,
          build_detail: true,
          order_outstanding: true,
          allocations: true
        },
        enableColumnSwitching: true,
        enableSearch: false,
        rowActions: rowActions,
        rowExpansion: rowExpansion,
        tableFilters: tableFilters
      }}
    />
  );
}
