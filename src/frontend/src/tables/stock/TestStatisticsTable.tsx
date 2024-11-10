import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import type { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

export function TestStatisticsTable({
  params = {}
}: Readonly<{ params?: any }>) {
  const initialColumns: TableColumn[] = [];
  const [templateColumnList, setTemplateColumnList] = useState(initialColumns);

  const testTemplateColumns: TableColumn[] = useMemo(() => {
    const data = templateColumnList ?? [];
    return data;
  }, [templateColumnList]);

  const tableColumns: TableColumn[] = useMemo(() => {
    const firstColumn: TableColumn = {
      accessor: 'col_0',
      title: '',
      sortable: true,
      switchable: false,
      noWrap: true
    };

    const lastColumn: TableColumn = {
      accessor: 'col_total',
      sortable: true,
      switchable: false,
      noWrap: true,
      title: t`Total`
    };

    return [firstColumn, ...testTemplateColumns, lastColumn];
  }, [testTemplateColumns]);

  function statCountString(count: number, total: number) {
    if (count > 0) {
      const percentage = ` (${((100.0 * count) / total).toLocaleString(
        undefined,
        {
          minimumFractionDigits: 0,
          maximumFractionDigits: 2
        }
      )}%)`;
      return count.toString() + percentage;
    }
    return '-';
  }

  // Format the test results based on the returned data
  const formatRecords = useCallback((records: any[]): any[] => {
    // interface needed to being able to dynamically assign keys
    interface ResultRow {
      [key: string]: string;
    }
    // Construct a list of test templates
    const results: ResultRow[] = [
      { id: 'row_passed', col_0: t`Passed` },
      { id: 'row_failed', col_0: t`Failed` },
      { id: 'row_total', col_0: t`Total` }
    ];
    let columnIndex = 0;

    columnIndex = 1;

    const newColumns: TableColumn[] = [];
    for (const key in records[0]) {
      if (key == 'total') continue;
      const acc = `col_${columnIndex.toString()}`;

      const resultKeys = ['passed', 'failed', 'total'];

      results[0][acc] = statCountString(
        records[0][key]['passed'],
        records[0][key]['total']
      );
      results[1][acc] = statCountString(
        records[0][key]['failed'],
        records[0][key]['total']
      );
      results[2][acc] = records[0][key]['total'].toString();

      newColumns.push({
        accessor: `col_${columnIndex.toString()}`,
        title: key
      });
      columnIndex++;
    }

    setTemplateColumnList(newColumns);

    results[0]['col_total'] = statCountString(
      records[0]['total']['passed'],
      records[0]['total']['total']
    );
    results[1]['col_total'] = statCountString(
      records[0]['total']['failed'],
      records[0]['total']['total']
    );
    results[2]['col_total'] = records[0]['total']['total'].toString();

    return results;
  }, []);

  const table = useTable('teststatistics');

  return (
    <InvenTreeTable
      url={`${apiUrl(params.apiEndpoint, params.pk)}/`}
      tableState={table}
      columns={tableColumns}
      props={{
        dataFormatter: formatRecords,
        enableDownload: false,
        enableSearch: false,
        enablePagination: false
      }}
    />
  );
}
