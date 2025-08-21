import { ApiEndpoints, apiUrl } from '@lib/index';
import { Group, Space } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import {
  DataTable,
  type DataTableRowExpansionProps,
  useDataTableColumns
} from 'mantine-datatable';
import { useMemo, useState } from 'react';
import { api } from '../../App';
import { RenderPartColumn } from '../ColumnRenderers';
import RowExpansionIcon from '../RowExpansionIcon';

/**
 * Display a nested subassembly table for a Bill of Materials (BOM).
 * - This component is used to render a subassembly table within a BOM.
 * - It is designed to be used within a larger BOM table structure.
 * - It may be rendered recursively, for multi-level subassemblies.
 */
export default function BomSubassemblyTable({
  columns,
  partId,
  depth
}: {
  columns: any[];
  partId: number | string;
  depth: number;
}) {
  const [expandedRecords, setExpandedRecords] = useState<string[]>([]);

  const assemblyColumns: any[] = useMemo(() => {
    return columns.map((col) => {
      // Handle the 'part' column differently based on depth and subassembly ID
      if (col.accessor == 'sub_part') {
        return {
          ...col,
          render: (record: any) => (
            <Group wrap='nowrap'>
              <Space w={depth * 10} />
              <RowExpansionIcon
                enabled={record.sub_part_detail?.assembly}
                expanded={expandedRecords.includes(record.pk)}
              />
              <RenderPartColumn part={record.sub_part_detail} />
            </Group>
          )
        };
      } else {
        return col;
      }
    });
  }, [columns, expandedRecords]);

  // Observe column widths from top-level BOM table
  const tableColumns = useDataTableColumns({
    key: 'table-bom',
    columns: assemblyColumns
  });

  const subassemblyData = useQuery({
    enabled: !!partId,
    queryKey: ['bomSubassembly', partId],
    queryFn: async () => {
      return api
        .get(apiUrl(ApiEndpoints.bom_list), {
          params: {
            part: partId,
            sub_part_detail: true
          }
        })
        .then((res) => res.data)
        .catch((err) => {
          console.error('Error fetching BOM subassembly data:', err);
          return [];
        });
    }
  });

  const rowExpansionProps: DataTableRowExpansionProps<any> = useMemo(() => {
    return {
      allowMultiple: true,
      expandable: ({ record }: { record: any }) =>
        record.sub_part_detail?.assembly,
      expanded: {
        recordIds: expandedRecords,
        onRecordIdsChange: setExpandedRecords
      },
      content: ({ record }: { record: any }) => (
        <BomSubassemblyTable
          columns={columns}
          partId={record.sub_part}
          depth={depth + 1}
        />
      )
    };
  }, [columns, depth, expandedRecords]);

  return (
    <DataTable
      noHeader
      withColumnBorders
      columns={tableColumns.effectiveColumns}
      records={subassemblyData.data || []}
      rowExpansion={rowExpansionProps}
    />
  );
}
