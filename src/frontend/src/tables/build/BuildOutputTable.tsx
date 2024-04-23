import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { TableColumn } from '../Column';
import { PartColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

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
  }, [testTemplates]);

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
          // TODO: Implement this!
          return '-';
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
          modelType: ModelType.stockitem
        }}
      />
    </>
  );
}
