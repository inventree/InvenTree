import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import {
  IconCircleCheck,
  IconCircleX,
  IconExclamationCircle
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';

import { api } from '../../App';
import { ProgressBar } from '../../components/items/ProgressBar';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { TableColumn } from '../Column';
import { PartColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';

type TestResultOverview = {
  name: string;
  result: boolean;
};

export default function BuildOutputTable({
  buildId,
  partId
}: {
  buildId: number;
  partId: number;
}) {
  const table = useTable('build-outputs');

  // Fetch the test templates associated with the partId
  const { data: testTemplates } = useQuery({
    queryKey: ['buildoutputtests', partId],
    queryFn: async () => {
      if (!partId) {
        return [];
      }

      return api
        .get(apiUrl(ApiEndpoints.part_test_template_list), {
          params: {
            part: partId,
            include_inherited: true,
            enabled: true,
            required: true
          }
        })
        .then((response) => response.data)
        .catch(() => []);
    }
  });

  const hasRequiredTests: boolean = useMemo(() => {
    return (testTemplates?.length ?? 0) > 0;
  }, [partId, testTemplates]);

  // Format table records
  const formatRecords = useCallback(
    (records: any[]): any[] => {
      records?.forEach((record: any, index: number) => {
        let results: TestResultOverview[] = [];
        let passCount: number = 0;

        // Iterate through each
        testTemplates?.forEach((template: any) => {
          // Find the "newest" result for this template in the returned data
          let result = record.tests
            ?.filter((test: any) => test.template == template.pk)
            .sort((a: any, b: any) => {
              return a.pk < b.pk ? 1 : -1;
            })
            .shift();

          if (template?.required && result?.result) {
            passCount += 1;
          }

          results.push({
            name: template.test_name,
            result: result?.result ?? false
          });
        });

        records[index].passCount = passCount;
        records[index].results = results;
      });

      return records;
    },
    [partId, testTemplates]
  );

  // TODO: Button to create new build output
  // TODO: Button to complete output(s)
  // TODO: Button to cancel output(s)
  // TODO: Button to scrap output(s)

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        sortable: true,
        render: (record: any) => PartColumn(record?.part_detail)
      },
      {
        accessor: 'quantity',
        ordering: 'stock',
        sortable: true,
        switchable: false,
        title: t`Build Output`,
        render: (record: any) => {
          let text = record.quantity;

          if (record.serial) {
            text = `# ${record.serial}`;
          }

          return (
            <Group position="left" noWrap>
              <Text>{text}</Text>
              {record.batch && (
                <Text italic size="sm">
                  {t`Batch`}: {record.batch}
                </Text>
              )}
            </Group>
          );
        }
      },
      {
        accessor: 'location',
        sortable: true,
        render: function (record: any) {
          // TODO: Custom renderer for location
          // TODO: Note, if not "In stock" we don't want to display the actual location here
          return record?.location_detail?.pathstring ?? record.location ?? '-';
        }
      },
      {
        accessor: 'allocations',
        sortable: false,
        switchable: false,
        title: t`Allocated Items`,
        render: (record: any) => {
          // TODO: Implement this!
          return '-';
        }
      },
      {
        accessor: 'tests',
        sortable: false,
        switchable: false,
        title: t`Required Tests`,
        hidden: !hasRequiredTests,
        render: (record: any) => {
          const extra =
            record.results?.map((result: TestResultOverview) => {
              return (
                result && (
                  <Group position="left" key={result.name} noWrap>
                    {result.result ? (
                      <IconCircleCheck color="green" />
                    ) : (
                      <IconCircleX color="red" />
                    )}
                    <Text>{result.name}</Text>
                  </Group>
                )
              );
            }) ?? [];

          return (
            <TableHoverCard
              value={
                <ProgressBar
                  progressLabel
                  value={record.passCount ?? 0}
                  maximum={testTemplates?.length ?? 0}
                />
              }
              extra={extra}
              title={t`Test Results`}
            />
          );
        }
      }
    ];
  }, [buildId, partId]);

  return (
    <>
      <InvenTreeTable
        tableState={table}
        url={apiUrl(ApiEndpoints.stock_item_list)}
        columns={tableColumns}
        props={{
          params: {
            part_detail: true,
            tests: true,
            is_building: true,
            build: buildId
          },
          modelType: ModelType.stockitem,
          dataFormatter: formatRecords
        }}
      />
    </>
  );
}
