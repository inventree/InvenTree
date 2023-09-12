import { randomId } from '@mantine/hooks';
import { useCallback, useState } from 'react';

/**
 * Custom hook for refreshing an InvenTreeTable externally
 * Returns a unique ID for the table, which can be updated to trigger a refresh of the <table className=""></table>
 *
 * @returns [refreshId, refreshTable]
 *
 * To use this hook:
 * const [refreshId, refreshTable] = useTableRefresh();
 *
 * Then, pass the refreshId to the InvenTreeTable component:
 * <InvenTreeTable refreshId={refreshId} ... />
 */
export function useTableRefresh() {
  const [refreshId, setRefreshId] = useState<string>(randomId());

  // Generate a new ID to refresh the table
  const refreshTable = useCallback(function () {
    setRefreshId(randomId());
  }, []);

  return { refreshId, refreshTable };
}
