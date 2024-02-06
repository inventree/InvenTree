import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo } from 'react';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

export default function StockItemTestResultTable({
  partId,
  itemId
}: {
  partId: number;
  itemId: number;
}) {
  const user = useUserState();
  const table = useTable('stocktests');

  // Query to fetch test templates associated with the part
  const testTemplates = useQuery({
    queryKey: ['testtemplates', partId],
    queryFn: async () => {
      if (!partId || !itemId) {
        return [];
      }

      return await api
        .get(apiUrl(ApiEndpoints.part_test_template_list), {
          params: {
            part: partId
          }
        })
        .then((response) => response.data)
        .catch(() => []);
    }
  });

  // Format the test results based on the returned data
  const formatRecords = useCallback(
    (records: any[]): any[] => {
      let resultMap: Record<string, any> = {};
      let resultList: any[] = [];

      // Iterate through the returned records
      // Note that the results are sorted by newest first,
      // to ensure that the most recent result is displayed "on top"
      records
        .sort((a, b) => {
          let aDate = new Date(a.date);
          let bDate = new Date(b.date);
          if (aDate < bDate) {
            return -1;
          } else if (aDate > bDate) {
            return 1;
          } else {
            return 0;
          }
        })
        .forEach((record, _idx) => {
          let key = record.key;

          // Most recent record is first
          if (!resultMap[key]) {
            resultMap[key] = record;
            resultMap[key]['old'] = [];
            resultMap[key]['template'] = testTemplates.data.find(
              (t: any) => t.key == key
            );
          } else {
            resultMap[key]['old'].push(record);
          }
        });

      // Now, re-create the original list of records
      records.forEach((record, _idx) => {
        let key = record.key;

        if (resultMap[key]) {
          resultList.push(resultMap[key]);
        }
      });

      // Also, check if there are any templates which have not been accounted for
      testTemplates.data.forEach((template: any) => {
        if (!resultMap[template.key]) {
          resultList.push({
            key: template.key,
            template: template
          });
        }
      });

      return records;
    },
    [testTemplates.data]
  );

  const tableColumns: TableColumn[] = useMemo(() => {
    return [];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.stock_test_result_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        dataFormatter: formatRecords,
        enablePagination: false,
        params: {
          stock_item: itemId,
          user_detail: true,
          attachment_detail: true
        }
      }}
    />
  );
}
