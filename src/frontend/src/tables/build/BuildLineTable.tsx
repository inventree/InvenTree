import { t } from '@lingui/core/macro';
import { Alert, Group, Paper, Text } from '@mantine/core';
import {
  IconArrowRight,
  IconCircleCheck,
  IconCircleDashedCheck,
  IconCircleMinus,
  IconCircleX,
  IconShoppingCart,
  IconTool,
  IconWand
} from '@tabler/icons-react';
import type { DataTableRowExpansionProps } from 'mantine-datatable';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ActionButton } from '@lib/components/ActionButton';
import { ProgressBar } from '@lib/components/ProgressBar';
import { RowEditAction, RowViewAction } from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { formatDecimal } from '@lib/functions/Formatting';
import type { TableFilter } from '@lib/types/Filters';
import type { RowAction, TableColumn } from '@lib/types/Tables';
import OrderPartsWizard from '../../components/wizards/OrderPartsWizard';
import {
  useAllocateStockToBuildForm,
  useBuildOrderFields,
  useConsumeBuildLinesForm
} from '../../forms/BuildForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  BooleanColumn,
  CategoryColumn,
  DecimalColumn,
  DescriptionColumn,
  LocationColumn,
  PartColumn,
  RenderPartColumn
} from '../ColumnRenderers';
import { PartCategoryFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
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
  const table = useTable('buildline-subtable');

  const tableColumns: any[] = useMemo(() => {
    return [
      PartColumn({
        part: 'part_detail'
      }),
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
      })
    ];
  }, []);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !onEditAllocation || !user.hasChangeRole(UserRoles.build),
          onClick: () => {
            onEditAllocation?.(record.pk);
          }
        }),
        {
          title: t`Remove`,
          tooltip: t`Remove allocated stock`,
          icon: <IconCircleX />,
          color: 'red',
          hidden: !onDeleteAllocation || !user.hasDeleteRole(UserRoles.build),
          onClick: () => {
            onDeleteAllocation?.(record.pk);
          }
        },
        RowViewAction({
          title: t`View Stock Item`,
          modelType: ModelType.stockitem,
          modelId: record.stock_item,
          navigate: navigate
        })
      ];
    },
    [user, onEditAllocation, onDeleteAllocation]
  );

  return (
    <Paper p='xs'>
      <InvenTreeTable
        tableState={table}
        columns={tableColumns}
        tableData={lineItem.filteredAllocations ?? lineItem.allocations}
        props={{
          minHeight: 200,
          enableSearch: false,
          enableRefresh: false,
          enableColumnSwitching: false,
          enableFilters: false,
          rowActions: rowActions,
          noRecordsText: ''
        }}
      />
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
        description: t`Show fully allocated lines`
      },
      {
        name: 'consumed',
        label: t`Consumed`,
        description: t`Show fully consumed lines`
      },
      {
        name: 'available',
        label: t`Available`,
        description: t`Show items with sufficient available stock`
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
      },
      {
        name: 'on_order',
        label: t`On Order`,
        description: t`Show items with stock on order`
      },
      PartCategoryFilter()
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
          {t`In production`}: {formatDecimal(record.in_production)}
        </Text>
      );
    }

    // Account for stock on order
    if (record.on_order > 0) {
      extra.push(
        <Text key='on-order' size='sm'>
          {t`On order`}: {formatDecimal(record.on_order)}
        </Text>
      );
    }

    // Account for "external" stock
    if (record.external_stock > 0) {
      extra.push(
        <Text key='external' size='sm'>
          {t`External stock`}: {formatDecimal(record.external_stock)}
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
            `${formatDecimal(available)}`
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
      PartColumn({
        accessor: 'bom_item',
        part: 'part_detail',
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
              <RenderPartColumn part={record.part_detail} />
            </Group>
          );
        }
      }),
      {
        accessor: 'part_detail.IPN',
        sortable: false,
        title: t`IPN`
      },
      CategoryColumn({
        accessor: 'category_detail',
        defaultVisible: false,
        switchable: true,
        sortable: true,
        ordering: 'category'
      }),
      DescriptionColumn({
        accessor: 'part_detail.description'
      }),
      {
        accessor: 'bom_item_detail.reference',
        ordering: 'reference',
        sortable: true,
        title: t`Reference`
      },
      BooleanColumn({
        accessor: 'bom_item_detail.optional',
        ordering: 'optional',
        hidden: hasOutput,
        defaultVisible: false
      }),
      BooleanColumn({
        accessor: 'bom_item_detail.consumable',
        ordering: 'consumable',
        hidden: hasOutput,
        defaultVisible: false
      }),
      BooleanColumn({
        accessor: 'bom_item_detail.allow_variants',
        ordering: 'allow_variants',
        hidden: hasOutput,
        defaultVisible: false
      }),
      BooleanColumn({
        accessor: 'bom_item_detail.inherited',
        ordering: 'inherited',
        title: t`Gets Inherited`,
        hidden: hasOutput,
        defaultVisible: false
      }),
      BooleanColumn({
        accessor: 'part_detail.trackable',
        ordering: 'trackable',
        hidden: hasOutput,
        defaultVisible: false
      }),
      {
        accessor: 'bom_item_detail.quantity',
        sortable: true,
        title: t`Unit Quantity`,
        defaultVisible: false,
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
        defaultVisible: false,
        switchable: false,
        render: (record: any) => {
          // Include information about the BOM item (if available)
          const extra: any[] = [];

          if (record?.bom_item_detail?.setup_quantity) {
            extra.push(
              <Text key='setup-quantity' size='sm'>
                {t`Setup Quantity`}:{' '}
                {formatDecimal(record.bom_item_detail.setup_quantity)}
              </Text>
            );
          }

          if (record?.bom_item_detail?.attrition) {
            extra.push(
              <Text key='attrition' size='sm'>
                {t`Attrition`}: {record.bom_item_detail.attrition}%
              </Text>
            );
          }

          if (record?.bom_item_detail?.rounding_multiple) {
            extra.push(
              <Text key='rounding-multiple' size='sm'>
                {t`Rounding Multiple`}:{' '}
                {record.bom_item_detail.rounding_multiple}
              </Text>
            );
          }

          // If a build output is specified, use the provided quantity
          return (
            <TableHoverCard
              title={t`BOM Information`}
              extra={extra}
              value={
                <Group justify='space-between' wrap='nowrap'>
                  <Text>{formatDecimal(record.requiredQuantity)}</Text>
                  {record?.part_detail?.units && (
                    <Text size='xs'>[{record.part_detail.units}]</Text>
                  )}
                </Group>
              }
            />
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
        accessor: 'in_production',
        sortable: true,
        ordering: 'scheduled_to_build',
        render: (record: any) => {
          if (record.scheduled_to_build > 0) {
            return (
              <ProgressBar
                progressLabel={true}
                value={record.in_production}
                maximum={record.scheduled_to_build}
              />
            );
          } else {
            return record.part_detail?.is_assembly ? 0 : '-';
          }
        }
      },
      DecimalColumn({
        accessor: 'on_order',
        defaultVisible: false,
        sortable: true
      }),
      {
        accessor: 'allocated',
        switchable: false,
        sortable: true,
        hidden: !isActive,
        minWidth: 125,
        render: (record: any) => {
          if (record?.bom_item_detail?.consumable) {
            return (
              <Text
                size='sm'
                style={{ fontStyle: 'italic' }}
              >{t`Consumable item`}</Text>
            );
          }

          const allocated = record.allocatedQuantity ?? 0;
          let required = Math.max(0, record.quantity - record.consumed);

          if (output?.pk) {
            // If an output is specified, we show the allocated quantity for that output
            required = record.bom_item_detail?.quantity;
          }

          if (allocated <= 0 && required <= 0) {
            return (
              <Group gap='xs' wrap='nowrap'>
                <IconCircleCheck size={16} color='green' />
                <Text size='sm' style={{ fontStyle: 'italic' }}>
                  {record.consumed >= record.quantity
                    ? t`Fully consumed`
                    : t`Fully allocated`}
                </Text>
              </Group>
            );
          }

          return (
            <ProgressBar
              progressLabel={true}
              value={allocated}
              maximum={required}
            />
          );
        }
      },
      {
        accessor: 'consumed',
        sortable: true,
        hidden: !!output?.pk,
        minWidth: 125,
        render: (record: any) => {
          return record?.bom_item_detail?.consumable ? (
            <Text style={{ fontStyle: 'italic' }}>{t`Consumable item`}</Text>
          ) : (
            <ProgressBar
              progressLabel={true}
              value={record.consumed}
              maximum={record.requiredQuantity}
            />
          );
        }
      }
    ];
  }, [hasOutput, isActive, table, output]);

  const buildOrderFields = useBuildOrderFields({
    create: true,
    modalId: 'new-build-order'
  });

  const [initialData, setInitialData] = useState<any>({});

  const [selectedLine, setSelectedLine] = useState<number | null>(null);

  const [selectedRows, setSelectedRows] = useState<any[]>([]);

  const newBuildOrder = useCreateApiFormModal({
    url: ApiEndpoints.build_order_list,
    title: t`Create Build Order`,
    fields: buildOrderFields,
    modalId: 'new-build-order',
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
    output: output,
    outputId: output?.pk ?? null,
    buildId: build.pk,
    lineItems: selectedRows,
    onFormSuccess: () => {
      table.clearSelectedRecords();
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
    onFormSuccess: () => {
      table.clearSelectedRecords();
      table.refreshTable();
    }
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
    onFormSuccess: table.refreshTable
  });

  const deleteAllocation = useDeleteApiFormModal({
    url: ApiEndpoints.build_item_list,
    pk: selectedAllocation,
    title: t`Remove Allocated Stock`,
    submitText: t`Remove`,
    onFormSuccess: table.refreshTable,
    preFormContent: (
      <Alert color='red' title={t`Confirm Removal`}>
        {t`Are you sure you want to remove this allocated stock from the order?`}
      </Alert>
    )
  });

  const [partsToOrder, setPartsToOrder] = useState<any[]>([]);

  const orderPartsWizard = OrderPartsWizard({
    parts: partsToOrder
  });

  const consumeLines = useConsumeBuildLinesForm({
    buildId: build.pk,
    buildLines: selectedRows,
    onFormSuccess: () => {
      table.clearSelectedRecords();
      table.refreshTable();
    }
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const part = record.part_detail ?? {};
      const in_production = build.status == buildStatus.PRODUCTION;
      const consumable: boolean = record.bom_item_detail?.consumable ?? false;
      const trackable: boolean = part?.trackable ?? false;

      const hasOutput: boolean = !!output?.pk;

      const required = Math.max(
        0,
        record.quantity - record.consumed - record.allocated
      );

      // Can consume
      const canConsume =
        in_production &&
        !consumable &&
        !trackable &&
        record.allocated > 0 &&
        user.hasChangeRole(UserRoles.build);

      // Can allocate
      const canAllocate =
        in_production &&
        !consumable &&
        user.hasChangeRole(UserRoles.build) &&
        required > 0 &&
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
        !consumable && user.hasAddRole(UserRoles.build) && part.assembly;

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
          icon: <IconCircleDashedCheck />,
          title: t`Consume Stock`,
          color: 'green',
          hidden: !canConsume || hasOutput,
          onClick: () => {
            setSelectedRows([record]);
            consumeLines.open();
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
      />,
      <ActionButton
        key='consume-stock'
        icon={<IconCircleDashedCheck />}
        tooltip={t`Consume Stock`}
        hidden={!visible || hasOutput}
        disabled={!table.hasSelectedRecords}
        color='green'
        onClick={() => {
          setSelectedRows(table.selectedRecords);
          consumeLines.open();
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
      {consumeLines.modal}
      {orderPartsWizard.wizard}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.build_line_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            ...params,
            build: build.pk,
            assembly_detail: false,
            bom_item_detail: true,
            category_detail: true,
            part_detail: true,
            allocations: true
          },
          tableActions: tableActions,
          tableFilters: tableFilters,
          rowActions: rowActions,
          dataFormatter: formatRecords,
          enableDownload: true,
          enableSelection: true,
          enableLabels: true,
          modelType: ModelType.buildline,
          detailAction: false,
          onCellClick: () => {},
          rowExpansion: rowExpansion
        }}
      />
    </>
  );
}
