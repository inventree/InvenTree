import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';

import { type RowAction, RowEditAction } from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { ActionButton, formatDecimal } from '@lib/index';
import type { TableFilter } from '@lib/types/Filters';
import type { StockOperationProps } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { Alert } from '@mantine/core';
import { IconCircleDashedCheck, IconCircleX } from '@tabler/icons-react';
import { useConsumeBuildItemsForm } from '../../forms/BuildForms';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useStockAdjustActions } from '../../hooks/UseStockAdjustActions';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  DecimalColumn,
  LocationColumn,
  PartColumn,
  ReferenceColumn,
  StatusColumn,
  StockColumn
} from '../ColumnRenderers';
import { IncludeVariantsFilter, StockLocationFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Render a table of allocated stock for a build.
 */
export default function BuildAllocatedStockTable({
  buildId,
  stockId,
  partId,
  showBuildInfo,
  showPartInfo,
  allowEdit,
  modelTarget,
  modelField
}: Readonly<{
  buildId?: number;
  stockId?: number;
  partId?: number;
  showPartInfo?: boolean;
  showBuildInfo?: boolean;
  allowEdit?: boolean;
  modelTarget?: ModelType;
  modelField?: string;
}>) {
  const user = useUserState();
  const table = useTable(
    !!partId ? 'buildallocatedstock-part' : 'buildallocatedstock'
  );

  const tableFilters: TableFilter[] = useMemo(() => {
    const filters: TableFilter[] = [
      {
        name: 'tracked',
        label: t`Allocated to Output`,
        description: t`Show items allocated to a build output`
      }
    ];

    if (!!partId) {
      filters.push(IncludeVariantsFilter());
    }

    filters.push(StockLocationFilter());

    return filters;
  }, [partId]);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      ReferenceColumn({
        accessor: 'build_detail.reference',
        title: t`Build Order`,
        switchable: false,
        hidden: showBuildInfo != true
      }),
      {
        accessor: 'build_detail.title',
        title: t`Description`,
        hidden: showBuildInfo != true
      },
      StatusColumn({
        accessor: 'build_detail.status',
        model: ModelType.build,
        title: t`Order Status`,
        hidden: showBuildInfo != true
      }),
      PartColumn({
        hidden: !showPartInfo,
        switchable: false
      }),
      {
        accessor: 'part_detail.IPN',
        ordering: 'IPN',
        hidden: !showPartInfo,
        title: t`IPN`,
        sortable: true,
        switchable: true
      },
      {
        hidden: !showPartInfo,
        accessor: 'bom_reference',
        title: t`Reference`,
        sortable: true,
        switchable: true
      },
      {
        accessor: 'batch',
        title: t`Batch Code`,
        sortable: false,
        switchable: true,
        render: (record: any) => record?.stock_item_detail?.batch
      },
      DecimalColumn({
        accessor: 'stock_item_detail.quantity',
        title: t`Available`
      }),
      {
        accessor: 'quantity',
        title: t`Allocated`,
        render: (record: any) => {
          const serial = record?.stock_item_detail?.serial;

          if (serial && record?.quantity == 1) {
            return `${t`Serial`}: ${serial}`;
          }

          return formatDecimal(record.quantity);
        }
      },
      LocationColumn({
        accessor: 'location_detail',
        switchable: true,
        sortable: true
      }),
      StockColumn({
        accessor: 'install_into_detail',
        title: t`Build Output`,
        sortable: false
      }),
      {
        accessor: 'sku',
        title: t`Supplier Part`,
        render: (record: any) => record?.supplier_part_detail?.SKU,
        sortable: true
      }
    ];
  }, []);

  const [selectedItemId, setSelectedItemId] = useState<number>(0);

  const editItem = useEditApiFormModal({
    pk: selectedItemId,
    url: ApiEndpoints.build_item_list,
    title: t`Edit Stock Allocation`,
    fields: {
      stock_item: {
        disabled: true
      },
      quantity: {}
    },
    table: table
  });

  const deleteItem = useDeleteApiFormModal({
    pk: selectedItemId,
    url: ApiEndpoints.build_item_list,
    title: t`Remove Allocated Stock`,
    submitText: t`Remove`,
    table: table,
    preFormContent: (
      <Alert color='red' title={t`Confirm Removal`}>
        {t`Are you sure you want to remove this allocated stock from the order?`}
      </Alert>
    )
  });

  const [selectedItems, setSelectedItems] = useState<any[]>([]);

  const itemsToConsume = useMemo(() => {
    return selectedItems.filter((item) => !item.part_detail?.trackable);
  }, [selectedItems]);

  const consumeStock = useConsumeBuildItemsForm({
    buildId: buildId ?? 0,
    allocatedItems: itemsToConsume,
    onFormSuccess: () => {
      table.clearSelectedRecords();
      table.refreshTable();
    }
  });

  const stockOperationProps: StockOperationProps = useMemo(() => {
    // Extract stock items from the selected records
    // Note that the table is actually a list of BuildItem instances,
    // so we need to reconstruct the stock item details
    const stockItems: any[] = table.selectedRecords
      .filter((item: any) => !!item.stock_item_detail)
      .map((item: any) => {
        return {
          ...item.stock_item_detail,
          part_detail: item.part_detail,
          location_detail: item.location_detail
        };
      });

    return {
      items: stockItems,
      model: ModelType.stockitem,
      refresh: table.refreshTable
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

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const part = record.part_detail ?? {};
      const trackable: boolean = part?.trackable ?? false;

      return [
        {
          color: 'green',
          icon: <IconCircleDashedCheck />,
          title: t`Consume`,
          tooltip: t`Consume Stock`,
          hidden: !buildId || trackable || !user.hasChangeRole(UserRoles.build),
          onClick: () => {
            setSelectedItems([record]);
            consumeStock.open();
          }
        },
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.build),
          onClick: () => {
            setSelectedItemId(record.pk);
            editItem.open();
          }
        }),
        {
          title: t`Remove`,
          tooltip: t`Remove allocated stock`,
          icon: <IconCircleX />,
          color: 'red',
          hidden: !user.hasDeleteRole(UserRoles.build),
          onClick: () => {
            setSelectedItemId(record.pk);
            deleteItem.open();
          }
        }
      ];
    },
    [user]
  );

  const tableActions = useMemo(() => {
    return [
      stockAdjustActions.dropdown,
      <ActionButton
        key='consume-stock'
        icon={<IconCircleDashedCheck />}
        tooltip={t`Consume Stock`}
        hidden={!user.hasChangeRole(UserRoles.build)}
        disabled={table.selectedRecords.length == 0}
        color='green'
        onClick={() => {
          setSelectedItems(table.selectedRecords);
          consumeStock.open();
        }}
      />
    ];
  }, [user, table.selectedRecords, stockAdjustActions.dropdown]);

  return (
    <>
      {editItem.modal}
      {deleteItem.modal}
      {consumeStock.modal}
      {stockAdjustActions.modals.map((modal) => modal.modal)}
      <InvenTreeTable
        tableState={table}
        url={apiUrl(ApiEndpoints.build_item_list)}
        columns={tableColumns}
        props={{
          params: {
            build: buildId,
            part: partId,
            stock_item: stockId,
            build_detail: showBuildInfo ?? false,
            part_detail: showPartInfo ?? false,
            location_detail: true,
            stock_detail: true,
            install_into_detail: true,
            supplier_detail: true
          },
          enableBulkDelete: allowEdit && user.hasDeleteRole(UserRoles.build),
          enableDownload: true,
          enableSelection: allowEdit && user.hasChangeRole(UserRoles.build),
          rowActions: rowActions,
          tableActions: tableActions,
          tableFilters: tableFilters,
          enableLabels: true,
          enableReports: true,
          printingAccessor: 'stock_item',
          modelField: modelField ?? 'stock_item',
          modelType: modelTarget ?? ModelType.stockitem
        }}
      />
    </>
  );
}
