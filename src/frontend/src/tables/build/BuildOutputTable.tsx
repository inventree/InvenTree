import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { IconCircleCheck, IconCircleX } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { api } from '../../App';
import { ActionButton } from '../../components/buttons/ActionButton';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ProgressBar } from '../../components/items/ProgressBar';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import {
  useBuildOrderOutputFields,
  useCancelBuildOutputsForm,
  useCompleteBuildOutputsForm,
  useScrapBuildOutputsForm
} from '../../forms/BuildForms';
import { InvenTreeIcon } from '../../functions/icons';
import { notYetImplemented } from '../../functions/notifications';
import { useCreateApiFormModal } from '../../hooks/UseForm';
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

export default function BuildOutputTable({ build }: { build: any }) {
  const user = useUserState();
  const table = useTable('build-outputs');

  const buildId: number = useMemo(() => {
    return build.pk ?? -1;
  }, [build.pk]);

  const partId: number = useMemo(() => {
    return build.part ?? -1;
  }, [build.part]);

  // Fetch the test templates associated with the partId
  const { data: testTemplates } = useQuery({
    queryKey: ['buildoutputtests', partId, build],
    queryFn: async () => {
      if (!partId || partId < 0) {
        return [];
      }

      // If the part is not testable, return an empty array
      if (!build?.part_detail?.testable) {
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

  // Fetch the "tracked" BOM items associated with the partId
  const { data: trackedItems } = useQuery({
    queryKey: ['trackeditems', buildId],
    queryFn: async () => {
      if (!buildId || buildId < 0) {
        return [];
      }

      return api
        .get(apiUrl(ApiEndpoints.build_line_list), {
          params: {
            build: buildId,
            tracked: true
          }
        })
        .then((response) => response.data)
        .catch(() => []);
    }
  });

  const hasTrackedItems: boolean = useMemo(() => {
    return (trackedItems?.length ?? 0) > 0;
  }, [trackedItems]);

  // Ensure base table data is updated correctly
  useEffect(() => {
    table.refreshTable();
  }, [hasTrackedItems, hasRequiredTests]);

  // Format table records
  const formatRecords = useCallback(
    (records: any[]): any[] => {
      records?.forEach((record: any, index: number) => {
        // Test result information, per record
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

        // Stock allocation information, per record
        let fullyAllocatedCount: number = 0;

        // Iterate through each tracked item
        trackedItems?.forEach((item: any) => {
          let allocated = 0;

          // Find all allocations which match the build output
          let allocations = item.allocations.filter(
            (allocation: any) => (allocation.install_into = record.pk)
          );

          allocations.forEach((allocation: any) => {
            allocated += allocation.quantity;
          });

          if (allocated >= item.bom_item_detail.quantity) {
            fullyAllocatedCount += 1;
          }
        });

        records[index].fullyAllocated = fullyAllocatedCount;
      });

      return records;
    },
    [partId, buildId, testTemplates, trackedItems]
  );

  const buildOutputFields = useBuildOrderOutputFields({ build: build });

  const addBuildOutput = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.build_output_create, buildId),
    title: t`Add Build Output`,
    fields: buildOutputFields,
    initialData: {
      batch_code: build.batch,
      location: build.destination ?? build.part_detail?.default_location
    },
    table: table
  });

  const [selectedOutputs, setSelectedOutputs] = useState<any[]>([]);

  const completeBuildOutputsForm = useCompleteBuildOutputsForm({
    build: build,
    outputs: selectedOutputs,
    onFormSuccess: () => {
      table.refreshTable();
    }
  });

  const scrapBuildOutputsForm = useScrapBuildOutputsForm({
    build: build,
    outputs: selectedOutputs,
    onFormSuccess: () => {
      table.refreshTable();
    }
  });

  const cancelBuildOutputsForm = useCancelBuildOutputsForm({
    build: build,
    outputs: selectedOutputs,
    onFormSuccess: () => {
      table.refreshTable();
    }
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        tooltip={t`Add Build Output`}
        hidden={!user.hasAddRole(UserRoles.build)}
        onClick={addBuildOutput.open}
      />,
      <ActionButton
        tooltip={t`Complete selected outputs`}
        icon={<InvenTreeIcon icon="success" />}
        color="green"
        disabled={!table.hasSelectedRecords}
        onClick={() => {
          setSelectedOutputs(table.selectedRecords);
          completeBuildOutputsForm.open();
        }}
      />,
      <ActionButton
        tooltip={t`Scrap selected outputs`}
        icon={<InvenTreeIcon icon="delete" />}
        color="red"
        disabled={!table.hasSelectedRecords}
        onClick={() => {
          setSelectedOutputs(table.selectedRecords);
          scrapBuildOutputsForm.open();
        }}
      />,
      <ActionButton
        tooltip={t`Cancel selected outputs`}
        icon={<InvenTreeIcon icon="cancel" />}
        color="red"
        disabled={!table.hasSelectedRecords}
        onClick={() => {
          setSelectedOutputs(table.selectedRecords);
          cancelBuildOutputsForm.open();
        }}
      />
    ];
  }, [user, table.selectedRecords, table.hasSelectedRecords]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        {
          title: t`Allocate`,
          tooltip: t`Allocate stock to build output`,
          color: 'blue',
          icon: <InvenTreeIcon icon="plus" />,
          onClick: notYetImplemented
        },
        {
          title: t`Deallocate`,
          tooltip: t`Deallocate stock from build output`,
          color: 'red',
          icon: <InvenTreeIcon icon="minus" />,
          onClick: notYetImplemented
        },
        {
          title: t`Complete`,
          tooltip: t`Complete build output`,
          color: 'green',
          icon: <InvenTreeIcon icon="success" />,
          onClick: () => {
            setSelectedOutputs([record]);
            completeBuildOutputsForm.open();
          }
        },
        {
          title: t`Scrap`,
          tooltip: t`Scrap build output`,
          icon: <InvenTreeIcon icon="delete" />,
          color: 'red',
          onClick: () => {
            setSelectedOutputs([record]);
            scrapBuildOutputsForm.open();
          }
        },
        {
          title: t`Cancel`,
          tooltip: t`Cancel build output`,
          icon: <InvenTreeIcon icon="cancel" />,
          color: 'red',
          onClick: () => {
            setSelectedOutputs([record]);
            cancelBuildOutputsForm.open();
          }
        }
      ];
    },
    [user, partId]
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
        hidden: !hasTrackedItems,
        title: t`Allocated Lines`,
        render: (record: any) => {
          return (
            <ProgressBar
              progressLabel
              value={record.fullyAllocated ?? 0}
              maximum={trackedItems?.length ?? 0}
            />
          );
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
  }, [
    buildId,
    partId,
    hasRequiredTests,
    hasTrackedItems,
    testTemplates,
    trackedItems
  ]);

  return (
    <>
      {addBuildOutput.modal}
      {completeBuildOutputsForm.modal}
      {scrapBuildOutputsForm.modal}
      {cancelBuildOutputsForm.modal}
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
