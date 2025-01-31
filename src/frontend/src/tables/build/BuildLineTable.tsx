import { t } from '@lingui/macro';
import { Alert, Group, Paper, Stack, Text } from '@mantine/core';
import {
  IconArrowRight,
  IconCircleMinus,
  IconShoppingCart,
  IconTool,
  IconWand
} from '@tabler/icons-react';
import { DataTable, type DataTableRowExpansionProps } from 'mantine-datatable';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ActionButton } from '../../components/buttons/ActionButton';
import { ProgressBar } from '../../components/items/ProgressBar';
import OrderPartsWizard from '../../components/wizards/OrderPartsWizard';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import {
  useAllocateStockToBuildForm,
  useBuildOrderFields
} from '../../forms/BuildForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import { BooleanColumn, LocationColumn, PartColumn } from '../ColumnRenderers';
import type { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import {
  type RowAction,
  RowActions,
  RowDeleteAction,
  RowEditAction,
  RowViewAction
} from '../RowActions';
import RowExpansionIcon from '../RowExpansionIcon';
import { TableHoverCard } from '../TableHoverCard';

/**
 * Render a sub-table of allocated stock against a particular build line.
 *
 * - Renders a simplified table of stock allocated against the build line
 * - Provides "edit" and "delete" actions for each allocation
 *
 * Note: We expect that the "lineItem" object contains an allocations[] list
 */
export function BuildLineSubTable({
  lineItem,
  onEditAllocation,
  onDeleteAllocation
}: Readonly<{
  lineItem: any;
  onEditAllocation?: (pk: number) => void;
  onDeleteAllocation?: (pk: number) => void;
}>) {
  const user = useUserState();
  const navigate = useNavigate();

  const tableColumns: any[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        title: t`Part`,
        render: (record: any) => {
          return <PartColumn part={record.part_detail} />;
        }
      },
      {
        accessor: 'quantity',
        title: t`Quantity`,
        render: (record: any) => {
          if (!!record.stock_item_detail?.serial) {
            return `# ${record.stock_item_detail.serial}`;
          }
          return record.quantity;
        }
      },
      {
        accessor: 'stock_item_detail.batch',
        title: t`Batch`
      },
      LocationColumn({
        accessor: 'location_detail'
      }),
      {
        accessor: '---actions---',
        title: ' ',
        width: 50,
        render: (record: any) => {
          return (
            <RowActions
              title={t`Actions`}
              index={record.pk}
              actions={[
                RowViewAction({
                  title: t`View Stock Item`,
                  modelType: ModelType.stockitem,
                  modelId: record.stock_item,
                  navigate: navigate
                }),
                RowEditAction({
                  hidden:
                    !onEditAllocation || !user.hasChangeRole(UserRoles.build),
                  onClick: () => {
                    onEditAllocation?.(record.pk);
                  }
                }),
                RowDeleteAction({
                  hidden:
                    !onDeleteAllocation || !user.hasDeleteRole(UserRoles.build),
                  onClick: () => {
                    onDeleteAllocation?.(record.pk);
                  }
                })
              ]}
            />
          );
        }
      }
    ];
  }, [user, onEditAllocation, onDeleteAllocation]);

  return (
    <Paper p='md'>
      <Stack gap='xs'>
        <DataTable
          minHeight={50}
          withTableBorder
          withColumnBorders
          striped
          pinLastColumn
          idAccessor='pk'
          columns={tableColumns}
          records={lineItem.filteredAllocations ?? lineItem.allocations}
        />
      </Stack>
    </Paper>
  );
}

/**
 * Render a table of build lines for a particular build.
 */
export default function BuildLineTable({
  build,
  output,
  params = {}
}: Readonly<{
  build: any;
  output?: any;
  params?: any;
}>) {
  const user = useUserState();
  const navigate = useNavigate();
  const buildStatus = useStatusCodes({ modelType: ModelType.build });

  const hasOutput: boolean = useMemo(() => !!output?.pk, [output]);

  const table = useTable(hasOutput ? 'buildline-output' : 'buildline');

  const isActive: boolean = useMemo(() => {
    return (
      build?.status == buildStatus.PRODUCTION ||
      build?.status == buildStatus.PENDING ||
      build?.status == buildStatus.ON_HOLD
    );
  }, [build, buildStatus]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'allocated',
        label: t`Allocated`,
        description: t`Show allocated lines`
      },
      {
        name: 'available',
        label: t`Available`,
        description: t`Show items with available stock`
      },
      {
        name: 'consumable',
        label: t`Consumable`,
        description: t`Show consumable lines`
      },
      {
        name: 'optional',
        label: t`Optional`,
        description: t`Show optional lines`
      },
      {
        name: 'assembly',
        label: t`Assembly`,
        description: t`Show assembled items`
      },
      {
        name: 'testable',
        label: t`Testable`,
        description: t`Show testable items`
      },
      {
        name: 'tracked',
        label: t`Tracked`,
        description: t`Show tracked lines`
      }
    ];
  }, []);

  const renderAvailableColumn = useCallback((record: any) => {
    const bom_item = record?.bom_item_detail ?? {};
    const extra: any[] = [];
    let available = record?.available_stock;

    // Account for substitute stock
    if (record.available_substitute_stock > 0) {
      available += record.available_substitute_stock;
      extra.push(
        <Text key='substitite' size='sm'>
          {t`Includes substitute stock`}
        </Text>
      );
    }

    // Account for variant stock
    if (bom_item.allow_variants && record.available_variant_stock > 0) {
      available += record.available_variant_stock;
      extra.push(
        <Text key='variant' size='sm'>
          {t`Includes variant stock`}
        </Text>
      );
    }

    // Account for in-production stock
    if (record.in_production > 0) {
      extra.push(
        <Text key='production' size='sm'>
          {t`In production`}: {record.in_production}
        </Text>
      );
    }

    // Account for stock on order
    if (record.on_order > 0) {
      extra.push(
        <Text key='on-order' size='sm'>
          {t`On order`}: {record.on_order}
        </Text>
      );
    }

    // Account for "external" stock
    if (record.external_stock > 0) {
      extra.push(
        <Text key='external' size='sm'>
          {t`External stock`}: {record.external_stock}
        </Text>
      );
    }

    const sufficient = available >= record.quantity - record.allocated;

    if (!sufficient) {
      extra.push(
        <Text key='insufficient' c='orange' size='sm'>
          {t`Insufficient stock`}
        </Text>
      );
    }

    return (
      <TableHoverCard
        icon={sufficient ? 'info' : 'exclamation'}
        iconColor={sufficient ? 'blue' : 'orange'}
        value={
          available > 0 ? (
            available
          ) : (
            <Text
              c='red'
              style={{ fontStyle: 'italic' }}
            >{t`No stock available`}</Text>
          )
        }
        title={t`Available Stock`}
        extra={extra}
      />
    );
  }, []);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'bom_item',
        title: t`Component`,
        ordering: 'part',
        sortable: true,
        switchable: false,
        render: (record: any) => {
          const hasAllocatedItems = record.allocatedQuantity > 0;

          return (
            <Group wrap='nowrap'>
              <RowExpansionIcon
                enabled={hasAllocatedItems}
                expanded={table.isRowExpanded(record.pk)}
              />
              <PartColumn part={record.part_detail} />
            </Group>
          );
        }
      },
      {
        accessor: 'part_detail.IPN',
        sortable: false,
        title: t`IPN`
      },
      {
        accessor: 'part_detail.description',
        sortable: false,
        title: t`Description`
      },
      {
        accessor: 'bom_item_detail.reference',
        ordering: 'reference',
        sortable: true,
        title: t`Reference`
      },
      BooleanColumn({
        accessor: 'bom_item_detail.optional',
        ordering: 'optional',
        hidden: hasOutput
      }),
      BooleanColumn({
        accessor: 'bom_item_detail.consumable',
        ordering: 'consumable',
        hidden: hasOutput
      }),
      BooleanColumn({
        accessor: 'bom_item_detail.allow_variants',
        ordering: 'allow_variants',
        hidden: hasOutput
      }),
      BooleanColumn({
        accessor: 'bom_item_detail.inherited',
        ordering: 'inherited',
        title: t`Gets Inherited`,
        hidden: hasOutput
      }),
      BooleanColumn({
        accessor: 'part_detail.trackable',
        ordering: 'trackable',
        hidden: hasOutput
      }),
      {
        accessor: 'bom_item_detail.quantity',
        sortable: true,
        title: t`Unit Quantity`,
        ordering: 'unit_quantity',
        render: (record: any) => {
          return (
            <Group justify='space-between' wrap='nowrap'>
              <Text>{record.bom_item_detail?.quantity}</Text>
              {record?.part_detail?.units && (
                <Text size='xs'>[{record.part_detail.units}]</Text>
              )}
            </Group>
          );
        }
      },
      {
        accessor: 'quantity',
        title: t`Required Quantity`,
        sortable: true,
        switchable: false,
        render: (record: any) => {
          // If a build output is specified, use the provided quantity
          return (
            <Group justify='space-between' wrap='nowrap'>
              <Text>{record.requiredQuantity}</Text>
              {record?.part_detail?.units && (
                <Text size='xs'>[{record.part_detail.units}]</Text>
              )}
            </Group>
          );
        }
      },
      {
        accessor: 'available_stock',
        sortable: true,
        switchable: false,
        render: renderAvailableColumn
      },
      {
        accessor: 'allocated',
        switchable: false,
        sortable: true,
        hidden: !isActive,
        render: (record: any) => {
          return record?.bom_item_detail?.consumable ? (
            <Text style={{ fontStyle: 'italic' }}>{t`Consumable item`}</Text>
          ) : (
            <ProgressBar
              progressLabel={true}
              value={record.allocatedQuantity}
              maximum={record.requiredQuantity}
            />
          );
        }
      }
    ];
  }, [hasOutput, isActive, table, output]);

  const buildOrderFields = useBuildOrderFields({ create: true });

  const [initialData, setInitialData] = useState<any>({});

  const [selectedLine, setSelectedLine] = useState<number | null>(null);

  const [selectedRows, setSelectedRows] = useState<any[]>([]);

  const newBuildOrder = useCreateApiFormModal({
    url: ApiEndpoints.build_order_list,
    title: t`Create Build Order`,
    fields: buildOrderFields,
    initialData: initialData,
    follow: true,
    modelType: ModelType.build
  });

  const autoAllocateStock = useCreateApiFormModal({
    url: ApiEndpoints.build_order_auto_allocate,
    pk: build.pk,
    title: t`Allocate Stock`,
    fields: {
      location: {
        filters: {
          structural: false
        }
      },
      exclude_location: {},
      interchangeable: {},
      substitutes: {},
      optional_items: {}
    },
    initialData: {
      location: build.take_from,
      interchangeable: true,
      substitutes: true,
      optional_items: false
    },
    successMessage: t`Auto allocation in progress`,
    table: table,
    preFormContent: (
      <Alert color='green' title={t`Auto Allocate Stock`}>
        <Text>{t`Automatically allocate stock to this build according to the selected options`}</Text>
      </Alert>
    )
  });

  const allocateStock = useAllocateStockToBuildForm({
    build: build,
    outputId: output?.pk ?? null,
    buildId: build.pk,
    lineItems: selectedRows,
    onFormSuccess: () => {
      table.refreshTable();
    }
  });

  const deallocateStock = useCreateApiFormModal({
    url: ApiEndpoints.build_order_deallocate,
    pk: build.pk,
    title: t`Deallocate Stock`,
    fields: {
      build_line: {
        hidden: true
      },
      output: {
        hidden: true
      }
    },
    initialData: {
      build_line: selectedLine,
      output: output?.pk ?? null
    },
    preFormContent: (
      <Alert color='red' title={t`Deallocate Stock`}>
        {selectedLine == undefined ? (
          <Text>{t`Deallocate all untracked stock for this build order`}</Text>
        ) : (
          <Text>{t`Deallocate stock from the selected line item`}</Text>
        )}
      </Alert>
    ),
    successMessage: t`Stock has been deallocated`,
    table: table
  });

  const [selectedAllocation, setSelectedAllocation] = useState<number>(0);

  const editAllocation = useEditApiFormModal({
    url: ApiEndpoints.build_item_list,
    pk: selectedAllocation,
    title: t`Edit Stock Allocation`,
    fields: {
      stock_item: {
        disabled: true
      },
      quantity: {}
    },
    table: table
  });

  const deleteAllocation = useDeleteApiFormModal({
    url: ApiEndpoints.build_item_list,
    pk: selectedAllocation,
    title: t`Delete Stock Allocation`,
    table: table
  });

  const [partsToOrder, setPartsToOrder] = useState<any[]>([]);

  const orderPartsWizard = OrderPartsWizard({
    parts: partsToOrder
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const part = record.part_detail ?? {};
      const in_production = build.status == buildStatus.PRODUCTION;
      const consumable = record.bom_item_detail?.consumable ?? false;

      const hasOutput = !!output?.pk;

      // Can allocate
      const canAllocate =
        in_production &&
        !consumable &&
        user.hasChangeRole(UserRoles.build) &&
        record.allocated < record.quantity &&
        record.trackable == hasOutput;

      // Can de-allocate
      const canDeallocate =
        in_production &&
        !consumable &&
        user.hasChangeRole(UserRoles.build) &&
        record.allocated > 0 &&
        record.trackable == hasOutput;

      const canOrder =
        !consumable &&
        user.hasAddRole(UserRoles.purchase_order) &&
        part.purchaseable;

      const canBuild =
        in_production &&
        !consumable &&
        user.hasAddRole(UserRoles.build) &&
        part.assembly;

      return [
        {
          icon: <IconArrowRight />,
          title: t`Allocate Stock`,
          hidden: !canAllocate,
          color: 'green',
          onClick: () => {
            setSelectedRows([record]);
            allocateStock.open();
          }
        },
        {
          icon: <IconCircleMinus />,
          title: t`Deallocate Stock`,
          hidden: !canDeallocate,
          color: 'red',
          onClick: () => {
            setSelectedLine(record.pk);
            deallocateStock.open();
          }
        },
        {
          icon: <IconShoppingCart />,
          title: t`Order Stock`,
          hidden: !canOrder,
          disabled: !table.hasSelectedRecords,
          color: 'blue',
          onClick: () => {
            setPartsToOrder([record.part_detail]);
            orderPartsWizard.openWizard();
          }
        },
        {
          icon: <IconTool />,
          title: t`Build Stock`,
          hidden: !canBuild,
          color: 'blue',
          onClick: () => {
            setInitialData({
              part: record.part,
              parent: build.pk,
              quantity: record.quantity - record.allocated
            });
            newBuildOrder.open();
          }
        },
        RowViewAction({
          title: t`View Part`,
          modelType: ModelType.part,
          modelId: record.part,
          navigate: navigate
        })
      ];
    },
    [user, navigate, output, build, buildStatus]
  );

  const tableActions = useMemo(() => {
    const production = build.status == buildStatus.PRODUCTION;
    const canEdit = user.hasChangeRole(UserRoles.build);
    const visible = production && canEdit;
    return [
      <ActionButton
        key='auto-allocate'
        icon={<IconWand />}
        tooltip={t`Auto Allocate Stock`}
        hidden={!visible || hasOutput}
        color='blue'
        onClick={() => {
          autoAllocateStock.open();
        }}
      />,
      <ActionButton
        key='order-parts'
        hidden={!user.hasAddRole(UserRoles.purchase_order)}
        disabled={!table.hasSelectedRecords}
        icon={<IconShoppingCart />}
        color='blue'
        tooltip={t`Order Parts`}
        onClick={() => {
          setPartsToOrder(
            table.selectedRecords
              .filter(
                (r) => r.part_detail?.purchaseable && r.part_detail?.active
              )
              .map((r) => r.part_detail)
          );
          orderPartsWizard.openWizard();
        }}
      />,
      <ActionButton
        key='allocate-stock'
        icon={<IconArrowRight />}
        tooltip={t`Allocate Stock`}
        hidden={!visible}
        disabled={!table.hasSelectedRecords}
        color='green'
        onClick={() => {
          let rows = table.selectedRecords
            .filter((r) => r.allocatedQuantity < r.requiredQuantity)
            .filter((r) => !r.bom_item_detail?.consumable);

          if (hasOutput) {
            rows = rows.filter((r) => r.trackable);
          } else {
            rows = rows.filter((r) => !r.trackable);
          }

          setSelectedRows(rows);
          allocateStock.open();
        }}
      />,
      <ActionButton
        key='deallocate-stock'
        icon={<IconCircleMinus />}
        tooltip={t`Deallocate Stock`}
        hidden={!visible || hasOutput}
        disabled={table.hasSelectedRecords}
        color='red'
        onClick={() => {
          setSelectedLine(null);
          deallocateStock.open();
        }}
      />
    ];
  }, [
    user,
    build,
    buildStatus,
    hasOutput,
    table.hasSelectedRecords,
    table.selectedRecords
  ]);

  /**
   * Format the records for the table, before rendering
   *
   * - Filter the "allocations" field to only show allocations for the selected output
   * - Pre-calculate the "requiredQuantity" and "allocatedQuantity" fields
   */
  const formatRecords = useCallback(
    (records: any[]): any[] => {
      return records.map((record) => {
        let allocations = [...record.allocations];

        // If an output is specified, filter the allocations to only show those for the selected output
        if (output?.pk) {
          allocations = allocations.filter((a) => a.install_into == output.pk);
        }

        let allocatedQuantity = 0;
        let requiredQuantity = record.quantity;

        // Calculate the total allocated quantity
        allocations.forEach((a) => {
          allocatedQuantity += a.quantity;
        });

        // Calculate the required quantity (based on the build output)
        if (output?.quantity && record.bom_item_detail) {
          requiredQuantity = output.quantity * record.bom_item_detail.quantity;
        }

        return {
          ...record,
          filteredAllocations: allocations,
          requiredQuantity: requiredQuantity,
          allocatedQuantity: allocatedQuantity
        };
      });
    },
    [output]
  );

  // Control row expansion
  const rowExpansion: DataTableRowExpansionProps<any> = useMemo(() => {
    return {
      allowMultiple: true,
      expandable: ({ record }: { record: any }) => {
        // Only items with allocated stock can be expanded
        return table.isRowExpanded(record.pk) || record.allocatedQuantity > 0;
      },
      content: ({ record }: { record: any }) => {
        return (
          <BuildLineSubTable
            lineItem={record}
            onEditAllocation={(pk: number) => {
              setSelectedAllocation(pk);
              editAllocation.open();
            }}
            onDeleteAllocation={(pk: number) => {
              setSelectedAllocation(pk);
              deleteAllocation.open();
            }}
          />
        );
      }
    };
  }, [table.isRowExpanded, output]);

  return (
    <>
      {autoAllocateStock.modal}
      {newBuildOrder.modal}
      {allocateStock.modal}
      {deallocateStock.modal}
      {editAllocation.modal}
      {deleteAllocation.modal}
      {orderPartsWizard.wizard}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.build_line_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            ...params,
            build: build.pk,
            part_detail: true
          },
          tableActions: tableActions,
          tableFilters: tableFilters,
          rowActions: rowActions,
          dataFormatter: formatRecords,
          enableDownload: true,
          enableSelection: true,
          rowExpansion: rowExpansion
        }}
      />
    </>
  );
}
