import { t } from '@lingui/core/macro';
import {
  Alert,
  Divider,
  Drawer,
  Group,
  Paper,
  Space,
  Stack,
  Text
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconBuildingFactory2,
  IconCircleCheck,
  IconCircleX,
  IconExclamationCircle
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { ActionButton } from '@lib/components/ActionButton';
import { AddItemButton } from '@lib/components/AddItemButton';
import { ProgressBar } from '@lib/components/ProgressBar';
import { type RowAction, RowEditAction } from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { StockOperationProps } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { StylishText } from '../../components/items/StylishText';
import { useApi } from '../../contexts/ApiContext';
import {
  useBuildOrderOutputFields,
  useCancelBuildOutputsForm,
  useCompleteBuildOutputsForm,
  useScrapBuildOutputsForm
} from '../../forms/BuildForms';
import {
  useStockFields,
  useStockItemSerializeFields
} from '../../forms/StockForms';
import { InvenTreeIcon } from '../../functions/icons';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { useStockAdjustActions } from '../../hooks/UseStockAdjustActions';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  LocationColumn,
  PartColumn,
  RenderPartColumn,
  StatusColumn
} from '../ColumnRenderers';
import {
  BatchFilter,
  HasBatchCodeFilter,
  IsSerializedFilter,
  SerialFilter,
  SerialGTEFilter,
  SerialLTEFilter,
  StatusFilterOptions,
  StockLocationFilter
} from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
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
        <Group p='xs' wrap='nowrap' justify='space-apart'>
          <StylishText size='lg'>{t`Build Output Stock Allocation`}</StylishText>
          <Space h='lg' />
          <Paper withBorder p='sm'>
            <Group gap='xs'>
              <RenderPartColumn part={build.part_detail} />
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
            </Group>
          </Paper>
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
  const table = useTable('build-outputs');

  const buildId: number = useMemo(() => {
    return build.pk ?? -1;
  }, [build.pk]);

  const partId: number = useMemo(() => {
    return build.part ?? -1;
  }, [build.part]);

  const buildStatus = useStatusCodes({ modelType: ModelType.build });

  // Fetch the test templates associated with the partId
  const { data: testTemplates, refetch: refetchTestTemplates } = useQuery({
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
        .then((response) => response.data);
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
            tracked: true,
            bom_item_detail: true,
            allocations: true
          }
        })
        .then((response) => response.data);
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

  const buildOutputFields = useBuildOrderOutputFields({
    build: build,
    modalId: 'add-build-output'
  });

  const addBuildOutput = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.build_output_create, buildId),
    title: t`Add Build Output`,
    modalId: 'add-build-output',
    fields: buildOutputFields,
    successMessage: t`Build output created`,
    timeout: 10000,
    initialData: {
      batch_code: build.batch,
      location: build.destination ?? build.part_detail?.default_location
    },
    onFormSuccess: () => {
      // Refresh all associated table data
      refetchTrackedItems();
      refetchTestTemplates();
      table.refreshTable(true);
    }
  });

  const [selectedOutputs, setSelectedOutputs] = useState<any[]>([]);

  const completeBuildOutputsForm = useCompleteBuildOutputsForm({
    build: build,
    outputs: selectedOutputs,
    onFormSuccess: () => {
      table.refreshTable(true);
      refreshBuild();
    }
  });

  const scrapBuildOutputsForm = useScrapBuildOutputsForm({
    build: build,
    outputs: selectedOutputs,
    onFormSuccess: () => {
      table.refreshTable(true);
      refreshBuild();
    }
  });

  const cancelBuildOutputsForm = useCancelBuildOutputsForm({
    build: build,
    outputs: selectedOutputs,
    onFormSuccess: () => {
      table.refreshTable(true);
      refreshBuild();
    }
  });

  const editStockItemFields = useStockFields({
    create: false,
    partId: partId,
    stockItem: selectedOutputs[0],
    modalId: 'edit-build-output'
  });

  const editBuildOutput = useEditApiFormModal({
    url: ApiEndpoints.stock_item_list,
    pk: selectedOutputs[0]?.pk,
    title: t`Edit Build Output`,
    modalId: 'edit-build-output',
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

  const serializeStockFields = useStockItemSerializeFields({
    partId: selectedOutputs[0]?.part,
    trackable: selectedOutputs[0]?.part_detail?.trackable,
    modalId: 'build-output-serialize'
  });

  const serializeOutput = useCreateApiFormModal({
    url: ApiEndpoints.stock_serialize,
    pk: selectedOutputs[0]?.pk,
    title: t`Serialize Build Output`,
    modalId: 'build-output-serialize',
    fields: serializeStockFields,
    initialData: {
      quantity: selectedOutputs[0]?.quantity ?? 1,
      destination: selectedOutputs[0]?.location ?? build.destination
    },
    onFormSuccess: () => {
      table.refreshTable(true);
      refreshBuild();
    }
  });

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'status',
        label: t`Status`,
        description: t`Filter by stock status`,
        choiceFunction: StatusFilterOptions(ModelType.stockitem)
      },
      StockLocationFilter(),
      HasBatchCodeFilter(),
      BatchFilter(),
      IsSerializedFilter(),
      SerialFilter(),
      SerialLTEFilter(),
      SerialGTEFilter()
    ];
  }, []);

  const stockOperationProps: StockOperationProps = useMemo(() => {
    return {
      items: table.selectedRecords,
      model: ModelType.stockitem,
      refresh: table.refreshTable,
      filters: {}
    };
  }, [table.selectedRecords, table.refreshTable]);

  const stockAdjustActions = useStockAdjustActions({
    formProps: stockOperationProps,
    merge: false,
    assign: false,
    delete: false,
    add: false,
    count: false,
    remove: false
  });

  const tableActions = useMemo(() => {
    return [
      stockAdjustActions.dropdown,
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
        icon={<InvenTreeIcon icon='scrap' />}
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
        hidden={build.external || !user.hasAddRole(UserRoles.build)}
        onClick={addBuildOutput.open}
      />
    ];
  }, [
    build,
    user,
    table.selectedRecords,
    table.hasSelectedRecords,
    stockAdjustActions.dropdown
  ]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const production = build?.status == buildStatus.PRODUCTION;

      return [
        {
          title: t`Allocate`,
          tooltip: t`Allocate stock to build output`,
          color: 'blue',
          hidden:
            !production ||
            !hasTrackedItems ||
            !user.hasChangeRole(UserRoles.build),
          icon: <InvenTreeIcon icon='plus' />,
          onClick: () => {
            setSelectedOutputs([record]);
            openAllocationDrawer();
          }
        },
        {
          title: t`Deallocate`,
          tooltip: t`Deallocate stock from build output`,
          color: 'red',
          hidden:
            !production ||
            !hasTrackedItems ||
            !user.hasChangeRole(UserRoles.build),
          icon: <InvenTreeIcon icon='minus' />,
          onClick: () => {
            setSelectedOutputs([record]);
            deallocateBuildOutput.open();
          }
        },
        {
          title: t`Serialize`,
          tooltip: t`Serialize build output`,
          color: 'blue',
          hidden: !record.part_detail?.trackable || !!record.serial,
          icon: <InvenTreeIcon icon='serial' />,
          onClick: () => {
            setSelectedOutputs([record]);
            serializeOutput.open();
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
          icon: <InvenTreeIcon icon='scrap' />,
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
    [buildStatus, user, partId, hasTrackedItems]
  );

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      PartColumn({}),
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

  const [
    allocationDrawerOpen,
    { open: openAllocationDrawer, close: closeAllocationDrawer }
  ] = useDisclosure(false);

  const closeDrawer = useCallback(() => {
    closeAllocationDrawer();
    refetchTrackedItems();
  }, [closeAllocationDrawer, refetchTrackedItems]);

  return (
    <>
      {addBuildOutput.modal}
      {completeBuildOutputsForm.modal}
      {scrapBuildOutputsForm.modal}
      {editBuildOutput.modal}
      {deallocateBuildOutput.modal}
      {cancelBuildOutputsForm.modal}
      {serializeOutput.modal}
      {stockAdjustActions.modals.map((modal) => modal.modal)}
      <OutputAllocationDrawer
        build={build}
        output={selectedOutputs[0]}
        opened={allocationDrawerOpen}
        close={closeDrawer}
      />
      <Stack gap='xs'>
        {build.external && (
          <Alert
            color='blue'
            icon={<IconBuildingFactory2 />}
            title={t`External Build`}
          >
            {t`This build order is fulfilled by an external purchase order`}
          </Alert>
        )}
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
            modelType: ModelType.stockitem,
            dataFormatter: formatRecords,
            tableFilters: tableFilters,
            tableActions: tableActions,
            rowActions: rowActions,
            enableSelection: true,
            onRowClick: (record: any) => {
              if (hasTrackedItems && !!record.serial) {
                setSelectedOutputs([record]);
                openAllocationDrawer();
              }
            }
          }}
        />
      </Stack>
    </>
  );
}
