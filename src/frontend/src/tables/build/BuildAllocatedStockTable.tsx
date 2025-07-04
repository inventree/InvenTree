import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { StockOperationProps } from '../../forms/StockForms';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useStockAdjustActions } from '../../hooks/UseStockAdjustActions';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import {
  LocationColumn,
  PartColumn,
  ReferenceColumn,
  StatusColumn
} from '../ColumnRenderers';
import { StockLocationFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

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
      filters.push({
        name: 'include_variants',
        type: 'boolean',
        label: t`Include Variants`,
        description: t`Include orders for part variants`
      });
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
      {
        accessor: 'part',
        hidden: !showPartInfo,
        title: t`Part`,
        sortable: true,
        switchable: false,
        render: (record: any) => PartColumn({ part: record.part_detail })
      },
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
        accessor: 'serial',
        title: t`Serial Number`,
        sortable: false,
        switchable: true,
        render: (record: any) => record?.stock_item_detail?.serial
      },
      {
        accessor: 'batch',
        title: t`Batch Code`,
        sortable: false,
        switchable: true,
        render: (record: any) => record?.stock_item_detail?.batch
      },
      {
        accessor: 'available',
        title: t`Available Quantity`,
        render: (record: any) => record?.stock_item_detail?.quantity
      },
      {
        accessor: 'quantity',
        title: t`Allocated Quantity`,
        sortable: true,
        switchable: false
      },
      LocationColumn({
        accessor: 'location_detail',
        switchable: true,
        sortable: true
      }),
      {
        accessor: 'install_into',
        title: t`Build Output`,
        sortable: true
      },
      {
        accessor: 'sku',
        title: t`Supplier Part`,
        render: (record: any) => record?.supplier_part_detail?.SKU,
        sortable: true
      }
    ];
  }, []);

  const [selectedItem, setSelectedItem] = useState<number>(0);

  const editItem = useEditApiFormModal({
    pk: selectedItem,
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
    pk: selectedItem,
    url: ApiEndpoints.build_item_list,
    title: t`Delete Stock Allocation`,
    table: table
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
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.build),
          onClick: () => {
            setSelectedItem(record.pk);
            editItem.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.build),
          onClick: () => {
            setSelectedItem(record.pk);
            deleteItem.open();
          }
        })
      ];
    },
    [user]
  );

  const tableActions = useMemo(() => {
    return [stockAdjustActions.dropdown];
  }, [stockAdjustActions.dropdown]);

  return (
    <>
      {editItem.modal}
      {deleteItem.modal}
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
            supplier_detail: true
          },
          enableBulkDelete: allowEdit && user.hasDeleteRole(UserRoles.build),
          enableDownload: true,
          enableSelection: allowEdit && user.hasDeleteRole(UserRoles.build),
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
