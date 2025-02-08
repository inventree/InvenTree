import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { IconCircleCheck, IconCircleDashedCheck } from '@tabler/icons-react';
import { ActionButton } from '../../components/buttons/ActionButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useConsumeBuildItemsForm } from '../../forms/BuildForms';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import {
  LocationColumn,
  PartColumn,
  ReferenceColumn,
  StatusColumn
} from '../ColumnRenderers';
import type { TableFilter } from '../Filter';
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
        accessor: 'quantity',
        title: t`Allocated Quantity`,
        sortable: true,
        switchable: false
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
    title: t`Delete Stock Allocation`,
    table: table
  });

  const [selectedItems, setSelectedItems] = useState<any[]>([]);

  const consumeStock = useConsumeBuildItemsForm({
    buildId: buildId ?? 0,
    allocatedItems: selectedItems,
    onFormSuccess: () => {
      table.refreshTable();
    }
  });

  const tableActions = useMemo(() => {
    return [
      <ActionButton
        key='consume-stock'
        icon={<IconCircleCheck />}
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
  }, [user, table.selectedRecords]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        {
          color: 'green',
          icon: <IconCircleDashedCheck />,
          title: t`Consume`,
          tooltip: t`Consume Stock`,
          hidden: !user.hasChangeRole(UserRoles.build),
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
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.build),
          onClick: () => {
            setSelectedItemId(record.pk);
            deleteItem.open();
          }
        })
      ];
    },
    [user]
  );

  return (
    <>
      {editItem.modal}
      {deleteItem.modal}
      {consumeStock.modal}
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
          modelField: modelField ?? 'stock_item',
          modelType: modelTarget ?? ModelType.stockitem
        }}
      />
    </>
  );
}
