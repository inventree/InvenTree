import { t } from '@lingui/macro';
import {
  Alert,
  Divider,
  Drawer,
  Group,
  Paper,
  Space,
  Text
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconCircleCheck,
  IconCircleX,
  IconExclamationCircle
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ActionButton } from '../../components/buttons/ActionButton';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ProgressBar } from '../../components/items/ProgressBar';
import { StylishText } from '../../components/items/StylishText';
import { useApi } from '../../contexts/ApiContext';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import {
  useBuildOrderOutputFields,
  useCancelBuildOutputsForm,
  useCompleteBuildOutputsForm,
  useScrapBuildOutputsForm
} from '../../forms/BuildForms';
import { useStockFields } from '../../forms/StockForms';
import { InvenTreeIcon } from '../../functions/icons';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import { LocationColumn, PartColumn, StatusColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowEditAction, RowViewAction } from '../RowActions';
import { TableHoverCard } from '../TableHoverCard';
import BuildLineTable from './BuildLineTable';

type TestResultOverview = {
  name: string;
  result: boolean;
};

/**
 * Detail drawer view for allocating stock against a specific build output
 */
function OutputAllocationDrawer({
  build,
  output,
  opened,
  close
}: Readonly<{
  build: any;
  output: any;
  opened: boolean;
  close: () => void;
}>) {
  return (
    <Drawer
      position='bottom'
      size='lg'
      title={
        <Group p='md' wrap='nowrap' justify='space-apart'>
          <StylishText size='lg'>{t`Build Output Stock Allocation`}</StylishText>
          <Space h='lg' />
          <PartColumn part={build.part_detail} />
          {output?.serial && (
            <Text size='sm'>
              {t`Serial Number`}: {output.serial}
            </Text>
          )}
          {output?.batch && (
            <Text size='sm'>
              {t`Batch Code`}: {output.batch}
            </Text>
          )}
          <Space h='lg' />
        </Group>
      }
      opened={opened}
      onClose={close}
      withCloseButton
      closeOnEscape
      closeOnClickOutside
      styles={{
        header: {
          width: '100%'
        },
        title: {
          width: '100%'
        }
      }}
    >
      <Divider />
      <Paper p='md'>
        <BuildLineTable
          build={build}
          output={output}
          params={{
            tracked: true
          }}
        />
      </Paper>
    </Drawer>
  );
}

export default function BuildOutputTable({
  build,
  refreshBuild
}: Readonly<{ build: any; refreshBuild: () => void }>) {
  const api = useApi();
  const user = useUserState();
  const navigate = useNavigate();
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
  const { data: trackedItems, refetch: refetchTrackedItems } = useQuery({
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
  }, [testTemplates, trackedItems, hasTrackedItems, hasRequiredTests]);

  // Format table records
  const formatRecords = useCallback(
    (records: any[]): any[] => {
      records?.forEach((record: any, index: number) => {
        // Test result information, per record
        const results: TestResultOverview[] = [];
        let passCount = 0;

        // Iterate through each
        testTemplates?.forEach((template: any) => {
          // Find the "newest" result for this template in the returned data
          const result = record.tests
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
        let fullyAllocatedCount = 0;

        // Iterate through each tracked item
        trackedItems?.forEach((item: any) => {
          let allocated = 0;

          // Find all allocations which match the build output
          item.allocations
            ?.filter((allocation: any) => allocation.install_into == record.pk)
            ?.forEach((allocation: any) => {
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
    timeout: 10000,
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
      refreshBuild();
    }
  });

  const scrapBuildOutputsForm = useScrapBuildOutputsForm({
    build: build,
    outputs: selectedOutputs,
    onFormSuccess: () => {
      table.refreshTable();
      refreshBuild();
    }
  });

  const cancelBuildOutputsForm = useCancelBuildOutputsForm({
    build: build,
    outputs: selectedOutputs,
    onFormSuccess: () => {
      table.refreshTable();
      refreshBuild();
    }
  });

  const editStockItemFields = useStockFields({
    create: false,
    partId: partId,
    stockItem: selectedOutputs[0]
  });

  const editBuildOutput = useEditApiFormModal({
    url: ApiEndpoints.stock_item_list,
    pk: selectedOutputs[0]?.pk,
    title: t`Edit Build Output`,
    fields: editStockItemFields,
    table: table
  });

  const deallocateBuildOutput = useCreateApiFormModal({
    url: ApiEndpoints.build_order_deallocate,
    pk: build.pk,
    title: t`Deallocate Stock`,
    preFormContent: (
      <Alert
        color='yellow'
        icon={<IconExclamationCircle />}
        title={t`Deallocate Stock`}
      >
        {t`This action will deallocate all stock from the selected build output`}
      </Alert>
    ),
    fields: {
      output: {
        hidden: true
      }
    },
    initialData: {
      output: selectedOutputs[0]?.pk
    },
    onFormSuccess: () => {
      refetchTrackedItems();
    }
  });

  const tableActions = useMemo(() => {
    return [
      <ActionButton
        key='complete-selected-outputs'
        tooltip={t`Complete selected outputs`}
        icon={<InvenTreeIcon icon='success' />}
        color='green'
        disabled={!table.hasSelectedRecords}
        onClick={() => {
          setSelectedOutputs(table.selectedRecords);
          completeBuildOutputsForm.open();
        }}
      />,
      <ActionButton
        key='scrap-selected-outputs'
        tooltip={t`Scrap selected outputs`}
        icon={<InvenTreeIcon icon='delete' />}
        color='red'
        disabled={!table.hasSelectedRecords}
        onClick={() => {
          setSelectedOutputs(table.selectedRecords);
          scrapBuildOutputsForm.open();
        }}
      />,
      <ActionButton
        key='cancel-selected-outputs'
        tooltip={t`Cancel selected outputs`}
        icon={<InvenTreeIcon icon='cancel' />}
        color='red'
        disabled={!table.hasSelectedRecords}
        onClick={() => {
          setSelectedOutputs(table.selectedRecords);
          cancelBuildOutputsForm.open();
        }}
      />,
      <AddItemButton
        key='add-build-output'
        tooltip={t`Add Build Output`}
        hidden={!user.hasAddRole(UserRoles.build)}
        onClick={addBuildOutput.open}
      />
    ];
  }, [user, table.selectedRecords, table.hasSelectedRecords]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowViewAction({
          title: t`View Build Output`,
          modelId: record.pk,
          modelType: ModelType.stockitem,
          navigate: navigate
        }),
        {
          title: t`Allocate`,
          tooltip: t`Allocate stock to build output`,
          color: 'blue',
          hidden: !hasTrackedItems || !user.hasChangeRole(UserRoles.build),
          icon: <InvenTreeIcon icon='plus' />,
          onClick: () => {
            setSelectedOutputs([record]);
            openDrawer();
          }
        },
        {
          title: t`Deallocate`,
          tooltip: t`Deallocate stock from build output`,
          color: 'red',
          hidden: !hasTrackedItems || !user.hasChangeRole(UserRoles.build),
          icon: <InvenTreeIcon icon='minus' />,
          onClick: () => {
            setSelectedOutputs([record]);
            deallocateBuildOutput.open();
          }
        },
        {
          title: t`Complete`,
          tooltip: t`Complete build output`,
          color: 'green',
          icon: <InvenTreeIcon icon='success' />,
          onClick: () => {
            setSelectedOutputs([record]);
            completeBuildOutputsForm.open();
          }
        },
        RowEditAction({
          tooltip: t`Edit Build Output`,
          onClick: () => {
            setSelectedOutputs([record]);
            editBuildOutput.open();
          }
        }),
        {
          title: t`Scrap`,
          tooltip: t`Scrap build output`,
          icon: <InvenTreeIcon icon='delete' />,
          color: 'red',
          onClick: () => {
            setSelectedOutputs([record]);
            scrapBuildOutputsForm.open();
          }
        },
        {
          title: t`Cancel`,
          tooltip: t`Cancel build output`,
          icon: <InvenTreeIcon icon='cancel' />,
          color: 'red',
          onClick: () => {
            setSelectedOutputs([record]);
            cancelBuildOutputsForm.open();
          }
        }
      ];
    },
    [user, partId, hasTrackedItems]
  );

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        sortable: true,
        render: (record: any) => PartColumn({ part: record?.part_detail })
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

          return text;
        }
      },
      {
        accessor: 'batch',
        sortable: true
      },
      StatusColumn({
        accessor: 'status',
        sortable: true,
        model: ModelType.stockitem
      }),
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
                  <Group justify='left' key={result.name} wrap='nowrap'>
                    {result.result ? (
                      <IconCircleCheck color='green' />
                    ) : (
                      <IconCircleX color='red' />
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

  const [drawerOpen, { open: openDrawer, close: closeDrawer }] =
    useDisclosure(false);

  return (
    <>
      {addBuildOutput.modal}
      {completeBuildOutputsForm.modal}
      {scrapBuildOutputsForm.modal}
      {editBuildOutput.modal}
      {deallocateBuildOutput.modal}
      {cancelBuildOutputsForm.modal}
      <OutputAllocationDrawer
        build={build}
        output={selectedOutputs[0]}
        opened={drawerOpen}
        close={closeDrawer}
      />
      <InvenTreeTable
        tableState={table}
        url={apiUrl(ApiEndpoints.stock_item_list)}
        columns={tableColumns}
        props={{
          params: {
            part_detail: true,
            location_detail: true,
            tests: true,
            is_building: true,
            build: buildId
          },
          enableLabels: true,
          enableReports: true,
          dataFormatter: formatRecords,
          tableActions: tableActions,
          rowActions: rowActions,
          enableSelection: true,
          onRowClick: (record: any) => {
            if (hasTrackedItems && !!record.serial) {
              setSelectedOutputs([record]);
              openDrawer();
            }
          }
        }}
      />
    </>
  );
}
