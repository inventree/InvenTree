import { useMemo } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

export default function StockItemTestResultTable({
  itemId
}: {
  itemId: number;
}) {
  const user = useUserState();
  const table = useTable('stocktests');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.stock_test_result_list)}
      tableState={table}
      columns={tableColumns}
      props={{}}
    />
  );
}
