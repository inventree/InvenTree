import { t } from '@lingui/macro';
import { Alert, Group, Text } from '@mantine/core';
import {
  IconArrowRight,
  IconCircleMinus,
  IconShoppingCart,
  IconTool,
  IconTransferIn,
  IconWand
} from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { ActionButton } from '../../components/buttons/ActionButton';
import { ProgressBar } from '../../components/items/ProgressBar';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import {
  useAllocateStockToBuildForm,
  useBuildOrderFields
} from '../../forms/BuildForms';
import { notYetImplemented } from '../../functions/notifications';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { BooleanColumn, PartColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction } from '../RowActions';
import { TableHoverCard } from '../TableHoverCard';

export default function BuildLineTable({
  buildId,
  build,
  outputId,
  params = {}
}: {
  buildId: number;
  build: any;
  outputId?: number;
  params?: any;
}) {
  const table = useTable('buildline');
  const user = useUserState();
  const buildStatus = useStatusCodes({ modelType: ModelType.build });

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
        description: t`Show lines with available stock`
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
    let bom_item = record?.bom_item_detail ?? {};
    let extra: any[] = [];
    let available = record?.available_stock;

    // Account for substitute stock
    if (record.available_substitute_stock > 0) {
      available += record.available_substitute_stock;
      extra.push(
        <Text key="substitite" size="sm">
          {t`Includes substitute stock`}
        </Text>
      );
    }

    // Account for variant stock
    if (bom_item.allow_variants && record.available_variant_stock > 0) {
      available += record.available_variant_stock;
      extra.push(
        <Text key="variant" size="sm">
          {t`Includes variant stock`}
        </Text>
      );
    }

    // Account for in-production stock
    if (record.in_production > 0) {
      extra.push(
        <Text key="production" size="sm">
          {t`In production`}: {record.in_production}
        </Text>
      );
    }

    // Account for stock on order
    if (record.on_order > 0) {
      extra.push(
        <Text key="on-order" size="sm">
          {t`On order`}: {record.on_order}
        </Text>
      );
    }

    // Account for "external" stock
    if (record.external_stock > 0) {
      extra.push(
        <Text key="external" size="sm">
          {t`External stock`}: {record.external_stock}
        </Text>
      );
    }

    const sufficient = available >= record.quantity - record.allocated;

    if (!sufficient) {
      extra.push(
        <Text key="insufficient" c="orange" size="sm">
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
              c="red"
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
        ordering: 'part',
        sortable: true,
        switchable: false,
        render: (record: any) => PartColumn(record.part_detail)
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
        ordering: 'optional'
      }),
      BooleanColumn({
        accessor: 'bom_item_detail.consumable',
        ordering: 'consumable'
      }),
      BooleanColumn({
        accessor: 'bom_item_detail.allow_variants',
        ordering: 'allow_variants'
      }),
      BooleanColumn({
        accessor: 'bom_item_detail.inherited',
        ordering: 'inherited',
        title: t`Gets Inherited`
      }),
      BooleanColumn({
        accessor: 'part_detail.trackable',
        ordering: 'trackable'
      }),
      {
        accessor: 'bom_item_detail.quantity',
        sortable: true,
        title: t`Unit Quantity`,
        ordering: 'unit_quantity',
        render: (record: any) => {
          return (
            <Group justify="space-between" wrap="nowrap">
              <Text>{record.bom_item_detail?.quantity}</Text>
              {record?.part_detail?.units && (
                <Text size="xs">[{record.part_detail.units}]</Text>
              )}
            </Group>
          );
        }
      },
      {
        accessor: 'quantity',
        sortable: true,
        switchable: false,
        render: (record: any) => {
          return (
            <Group justify="space-between" wrap="nowrap">
              <Text>{record.quantity}</Text>
              {record?.part_detail?.units && (
                <Text size="xs">[{record.part_detail.units}]</Text>
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
        render: (record: any) => {
          return record?.bom_item_detail?.consumable ? (
            <Text style={{ fontStyle: 'italic' }}>{t`Consumable item`}</Text>
          ) : (
            <ProgressBar
              progressLabel={true}
              value={record.allocated}
              maximum={record.quantity}
            />
          );
        }
      }
    ];
  }, []);

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
      <Alert color="green" title={t`Auto Allocate Stock`}>
        <Text>{t`Automatically allocate stock to this build according to the selected options`}</Text>
      </Alert>
    )
  });

  const allowcateStock = useAllocateStockToBuildForm({
    build: build,
    outputId: null,
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
        hidden: true,
        value: null
      }
    },
    initialData: {
      build_line: selectedLine
    },
    preFormContent: (
      <Alert color="red" title={t`Deallocate Stock`}>
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

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      let part = record.part_detail ?? {};

      // Consumable items have no appropriate actions
      if (record?.bom_item_detail?.consumable) {
        return [];
      }

      // Only allow actions when build is in production
      if (!build?.status || build.status != buildStatus.PRODUCTION) {
        return [];
      }

      const hasOutput = !!outputId;

      // Can allocate
      let canAllocate =
        user.hasChangeRole(UserRoles.build) &&
        record.allocated < record.quantity &&
        record.trackable == hasOutput;

      // Can de-allocate
      let canDeallocate =
        user.hasChangeRole(UserRoles.build) &&
        record.allocated > 0 &&
        record.trackable == hasOutput;

      let canOrder =
        user.hasAddRole(UserRoles.purchase_order) && part.purchaseable;
      let canBuild = user.hasAddRole(UserRoles.build) && part.assembly;

      return [
        {
          icon: <IconArrowRight />,
          title: t`Allocate Stock`,
          hidden: !canAllocate,
          color: 'green',
          onClick: () => {
            setSelectedRows([record]);
            allowcateStock.open();
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
          onClick: notYetImplemented
        },
        {
          icon: <IconTool />,
          title: t`Build Stock`,
          hidden: !canBuild,
          color: 'blue',
          onClick: () => {
            setInitialData({
              part: record.part,
              parent: buildId,
              quantity: record.quantity - record.allocated
            });
            newBuildOrder.open();
          }
        }
      ];
    },
    [user, outputId, build, buildStatus]
  );

  const tableActions = useMemo(() => {
    const production = build.status == buildStatus.PRODUCTION;
    const canEdit = user.hasChangeRole(UserRoles.build);
    const visible = production && canEdit;
    return [
      <ActionButton
        icon={<IconWand />}
        tooltip={t`Auto Allocate Stock`}
        hidden={!visible}
        color="blue"
        onClick={() => {
          autoAllocateStock.open();
        }}
      />,
      <ActionButton
        icon={<IconArrowRight />}
        tooltip={t`Allocate Stock`}
        hidden={!visible}
        disabled={!table.hasSelectedRecords}
        color="green"
        onClick={() => {
          setSelectedRows(
            table.selectedRecords.filter(
              (r) =>
                r.allocated < r.quantity &&
                !r.trackable &&
                !r.bom_item_detail.consumable
            )
          );
          allowcateStock.open();
        }}
      />,
      <ActionButton
        icon={<IconCircleMinus />}
        tooltip={t`Deallocate Stock`}
        hidden={!visible}
        disabled={table.hasSelectedRecords}
        color="red"
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
    table.hasSelectedRecords,
    table.selectedRecords
  ]);

  return (
    <>
      {autoAllocateStock.modal}
      {newBuildOrder.modal}
      {allowcateStock.modal}
      {deallocateStock.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.build_line_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            ...params,
            build: buildId,
            part_detail: true
          },
          tableActions: tableActions,
          tableFilters: tableFilters,
          rowActions: rowActions,
          enableDownload: true,
          enableSelection: true
        }}
      />
    </>
  );
}
