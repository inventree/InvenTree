import { ApiEndpoints, apiUrl } from '@lib/index';
import { Group, Space } from '@mantine/core';
import { useLocalStorage } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import {
  DataTable,
  type DataTableColumn,
  type DataTableRowExpansionProps
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

  // Observe column widths from top-level BOM table
  const [columnWidths] = useLocalStorage({
    key: 'table-bom-columns-width',
    defaultValue: []
  });

  const assemblyColumns: DataTableColumn[] = useMemo(() => {
    return columns.map((col) => {
      // Handle the 'part' column differently based on depth and subassembly ID
      const column = { ...col };

      if (col.accessor == 'sub_part') {
        column.render = (record: any) => (
          <Group wrap='nowrap'>
            <Space w={depth * 10} />
            {record.sub_part_detail?.assembly && (
              <RowExpansionIcon
                enabled={record.sub_part_detail?.assembly}
                expanded={expandedRecords.includes(record.pk)}
              />
            )}
            <RenderPartColumn part={record.sub_part_detail} />
          </Group>
        );
      }

      // Find matching column width
      const matchingWidth = columnWidths.find(
        (cw: any) => Object.keys(cw)[0] === col.accessor
      );

      if (matchingWidth) {
        column.cellsStyle = (record: any, index: number) => {
          return {
            width: Object.values(matchingWidth)[0]
          };
        };
      }

      return column;
    });
  }, [columns, columnWidths, expandedRecords]);

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
      columns={assemblyColumns}
      // columns={tableColumns.effectiveColumns}
      records={subassemblyData.data || []}
      rowExpansion={rowExpansionProps}
    />
  );
}
