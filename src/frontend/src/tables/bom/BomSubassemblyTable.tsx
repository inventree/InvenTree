import { ApiEndpoints, apiUrl } from '@lib/index';
import { useQuery } from '@tanstack/react-query';
import { DataTable, useDataTableColumns } from 'mantine-datatable';
import { useState } from 'react';
import { api } from '../../App';

/**
 * Display a nested subassembly table for a Bill of Materials (BOM).
 * - This component is used to render a subassembly table within a BOM.
 * - It is designed to be used within a larger BOM table structure.
 * - It may be rendered recursively, for multi-level subassemblies.
 */
export default function BomSubassemblyTable({
  columns,
  partId
}: {
  columns: any[];
  partId: number | string;
}) {
  const [expandedRecords, setExpandedRecords] = useState<string[]>([]);

  // Observe column widths from parent table
  const tableColumns = useDataTableColumns({
    key: 'table-bom',
    columns: columns
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

  return (
    <DataTable
      noHeader
      withColumnBorders
      columns={tableColumns.effectiveColumns}
      records={subassemblyData.data || []}
      // rowExpansion={{
      //     allowMultiple: true,
      //     expanded: {
      //         recordIds: expandedRecords,
      //         onRecordIdsChange: setExpandedRecords,
      //     },
      //     content: (subassembly: any) => (
      //         <BomSubassemblyTable
      //             columns={columns}
      //             partId={subassembly.sub_part}
      //         />
      //     )
      // }}
    />
  );
}
