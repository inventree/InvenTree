import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { DataTableRowExpansionProps } from 'mantine-datatable';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ProgressBar } from '../../components/items/ProgressBar';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { StatusColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowViewAction } from '../RowActions';
import RowExpansionIcon from '../RowExpansionIcon';
import { BuildLineSubTable } from '../build/BuildLineTable';

/**
 * A "simplified" BuildOrderLineItem table showing all outstanding build order allocations for a given part.
 */
export default function PartBuildAllocationsTable({
  partId
}: {
  partId: number;
}) {
  const user = useUserState();
  const navigate = useNavigate();
  const table = useTable('part-build-allocations');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'build',
        title: t`Build Order`,
        sortable: true,
        render: (record: any) => (
          <Group wrap="nowrap" gap="xs">
            <RowExpansionIcon
              enabled={record.allocated > 0}
              expanded={table.isRowExpanded(record.pk)}
            />
            <Text>{record.build_detail?.reference}</Text>
          </Group>
        )
      },
      StatusColumn({
        accessor: 'build_detail.status',
        model: ModelType.build,
        title: t`Order Status`
      }),
      {
        accessor: 'allocated',
        sortable: true,
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
        return (
          <BuildLineSubTable
            lineItem={record}
            onEditAllocation={(pk: number) => {
              //   setSelectedAllocation(pk);
              //   editAllocation.open();
            }}
            onDeleteAllocation={(pk: number) => {
              //   setSelectedAllocation(pk);
              //   deleteAllocation.open();
            }}
          />
        );
      }
    };
  }, [table.isRowExpanded]);

  return (
    <>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.build_line_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            part: partId,
            consumable: false,
            build_detail: true,
            order_outstanding: true
          },
          enableDownload: true,
          rowActions: rowActions,
          rowExpansion: rowExpansion
        }}
      />
    </>
  );
}
