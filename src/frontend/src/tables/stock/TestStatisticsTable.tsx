import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { stockLocationFields } from '../../forms/StockForms';
import { getDetailUrl } from '../../functions/urls';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { BooleanColumn, DescriptionColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export function TestStatisticsTable({ params = {} }: { params?: any }) {
  const initialColumns: TableColumn[] = [];
  const [templateColumnList, setTemplateColumnList] = useState(initialColumns);

  const testTemplateColumns: TableColumn[] = useMemo(() => {
    let data = templateColumnList ?? [];
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
      let percentage =
        ' (' +
        ((100.0 * count) / total).toLocaleString(undefined, {
          minimumFractionDigits: 0,
          maximumFractionDigits: 2
        }) +
        '%)';
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
    let results: ResultRow[] = [
      { id: 'row_passed', col_0: t`Passed` },
      { id: 'row_failed', col_0: t`Failed` },
      { id: 'row_total', col_0: t`Total` }
    ];
    let columnIndex = 0;

    columnIndex = 1;

    let newColumns: TableColumn[] = [];
    for (let key in records[0]) {
      if (key == 'total') continue;
      let acc = 'col_' + columnIndex.toString();

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
        accessor: 'col_' + columnIndex.toString(),
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
      url={apiUrl(params.apiEndpoint, params.pk) + '/'}
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
