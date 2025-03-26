import { useCallback, useEffect, useState } from 'react';

/**
 * Hook to manage multiple selected rows in a multi-action modal.
 *
 * - The hook is initially provided with a list of rows
 * - A callback is provided to remove a row, based on the provided ID value
 */
export function useSelectedRows<T>({
  rows,
  pkField = 'pk'
}: {
  rows: T[];
  pkField?: string;
}) {
  const [selectedRows, setSelectedRows] = useState<T[]>(rows);

  // Update selection whenever input rows are updated
  useEffect(() => {
    setSelectedRows(rows);
  }, [rows]);

  // Callback to remove the selected row
  const removeRow = useCallback(
    (pk: any) => {
      setSelectedRows((rows) =>
        rows.filter((row: any) => row[pkField ?? 'pk'] !== pk)
      );
    },
    [pkField]
  );

  return {
    selectedRows,
    removeRow
  };
}
