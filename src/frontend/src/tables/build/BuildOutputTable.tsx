import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { IconCircleCheck, IconCircleX } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';

import { api } from '../../App';
import { ActionButton } from '../../components/buttons/ActionButton';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ProgressBar } from '../../components/items/ProgressBar';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { InvenTreeIcon } from '../../functions/icons';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { LocationColumn, PartColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction } from '../RowActions';
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
  const user = useUserState();
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

  const tableActions = useMemo(() => {
    // TODO: Button to create new build output
    // TODO: Button to complete output(s)
    // TODO: Button to cancel output(s)
    // TODO: Button to scrap output(s)
    return [
      <AddItemButton
        tooltip={t`Add Build Output`}
        hidden={!user.hasAddRole(UserRoles.build)}
      />,
      <ActionButton
        tooltip={t`Complete selected outputs`}
        icon={<InvenTreeIcon icon="success" />}
        color="green"
        disabled={!table.hasSelectedRecords}
      />,
      <ActionButton
        tooltip={t`Scrap selected outputs`}
        icon={<InvenTreeIcon icon="delete" />}
        color="red"
        disabled={!table.hasSelectedRecords}
      />,
      <ActionButton
        tooltip={t`Cancel selected outputs`}
        icon={<InvenTreeIcon icon="cancel" />}
        color="red"
        disabled={!table.hasSelectedRecords}
      />
    ];
  }, [user, partId, buildId, table.hasSelectedRecords]);

  const rowActions = useCallback(
    (record: any) => {
      let actions: RowAction[] = [
        {
          title: t`Allocate`,
          tooltip: t`Allocate stock to build output`,
          color: 'blue',
          icon: <InvenTreeIcon icon="plus" />
        },
        {
          title: t`Deallocate`,
          tooltip: t`Deallocate stock from build output`,
          color: 'red',
          icon: <InvenTreeIcon icon="minus" />
        },
        {
          title: t`Complete`,
          tooltip: t`Complete build output`,
          color: 'green',
          icon: <InvenTreeIcon icon="success" />
        },
        {
          title: t`Scrap`,
          tooltip: t`Scrap build output`,
          icon: <InvenTreeIcon icon="delete" />,
          color: 'red'
        },
        {
          title: t`Cancel`,
          tooltip: t`Cancel build output`,
          icon: <InvenTreeIcon icon="cancel" />,
          color: 'red'
        }
      ];

      return actions;
    },
    [user, partId, buildId]
  );

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
            <Group justify="left" wrap="nowrap">
              <Text>{text}</Text>
              {record.batch && (
                <Text style={{ fontStyle: 'italic' }} size="sm">
                  {t`Batch`}: {record.batch}
                </Text>
              )}
            </Group>
          );
        }
      },
      LocationColumn({
        accessor: 'location_detail'
      }),
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
                  <Group justify="left" key={result.name} wrap="nowrap">
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
          dataFormatter: formatRecords,
          tableActions: tableActions,
          rowActions: rowActions,
          enableSelection: true
        }}
      />
    </>
  );
}
