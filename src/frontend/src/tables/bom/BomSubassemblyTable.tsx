import { ApiEndpoints, ModelType, apiUrl, useTable } from '@lib/index';
import type { TableColumn, TableState } from '@lib/types/Tables';
import { Group, Paper } from '@mantine/core';
import { useMemo } from 'react';
import {
  IPNColumn,
  ReferenceColumn,
  RenderPartColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import RowExpansionIcon from '../RowExpansionIcon';

export function subassemblyRowExpansion({
  table
}: {
  table: TableState;
}) {
  return useMemo(() => {
    return {
      allowMultiple: true,
      expandable: ({ record }: { record: any }) => {
        return (
          table.isRowExpanded(record.pk) || !!record.sub_part_detail?.assembly
        );
      },
      content: ({ record }: { record: any }) => {
        return <BomSubassemblyTable partId={record.sub_part} />;
      }
    };
  }, [table.isRowExpanded]);
}

/**
 * Display a sub-table of the BOM, for displaying sub-assemblies within the main BOM table.
 */
export default function BomSubassemblyTable({
  partId
}: {
  partId: number;
}) {
  const table = useTable('bom-subassembly');

  const rowExpansion = subassemblyRowExpansion({ table: table });

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'sub_part',
        render: (record: any) => {
          return (
            <Group gap='xs' justify='left' p={0}>
              {record.sub_part_detail?.assembly && (
                <RowExpansionIcon
                  enabled
                  expanded={table.isRowExpanded(record.pk)}
                />
              )}
              <RenderPartColumn part={record.sub_part_detail} />
            </Group>
          );
        }
      },
      IPNColumn({
        accessor: 'sub_part_detail.IPN'
      }),
      ReferenceColumn({}),
      {
        accessor: 'quantity'
      }
    ];
  }, [table.isRowExpanded]);

  return (
    <Paper p={'xs'}>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.bom_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          modelType: ModelType.part,
          modelField: 'sub_part',
          onCellClick: () => {},
          rowExpansion: rowExpansion,
          enableSearch: false,
          enableFilters: false,
          enableColumnSwitching: false,
          enableRefresh: false,
          enableReports: false,
          params: {
            part: partId,
            substitutes: false,
            part_detail: true,
            sub_part_detail: true
          }
        }}
      />
    </Paper>
  );
}
