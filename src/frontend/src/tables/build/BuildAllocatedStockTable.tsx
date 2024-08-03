import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { LocationColumn, PartColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../RowActions';

/**
 * Render a table of allocated stock for a build.
 */
export default function BuildAllocatedStockTable({
  buildId
}: {
  buildId: number;
}) {
  const user = useUserState();
  const table = useTable('build-allocated-stock');

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'tracked',
        label: t`Allocated to Output`,
        description: t`Show items allocated to a build output`
      }
    ];
  }, []);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        title: t`Part`,
        sortable: true,
        switchable: false,
        render: (record: any) => PartColumn(record.part_detail)
      },
      {
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

  const [selectedItem, setSelectedItem] = useState<number>(0);

  const editItem = useEditApiFormModal({
    pk: selectedItem,
    url: ApiEndpoints.build_item_list,
    title: t`Edit Build Item`,
    fields: {
      quantity: {}
    },
    table: table
  });

  const deleteItem = useDeleteApiFormModal({
    pk: selectedItem,
    url: ApiEndpoints.build_item_list,
    title: t`Delete Build Item`,
    table: table
  });

  const rowActions = useCallback(
    (record: any) => {
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

  return (
    <>
      {editItem.modal}
      {deleteItem.modal}
      <InvenTreeTable
        tableState={table}
        url={apiUrl(ApiEndpoints.build_item_list)}
        columns={tableColumns}
        props={{
          params: {
            build: buildId,
            part_detail: true,
            location_detail: true,
            stock_detail: true,
            supplier_detail: true
          },
          enableBulkDelete: user.hasDeleteRole(UserRoles.build),
          enableDownload: true,
          enableSelection: true,
          rowActions: rowActions,
          tableFilters: tableFilters,
          modelField: 'stock_item',
          modelType: ModelType.stockitem
        }}
      />
    </>
  );
}
