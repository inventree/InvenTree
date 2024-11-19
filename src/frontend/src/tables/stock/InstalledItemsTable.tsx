import { t } from '@lingui/macro';
import { Skeleton } from '@mantine/core';
import { IconUnlink } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import {
  useStockItemInstallFields,
  useStockItemUninstallFields
} from '../../forms/StockForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import { PartColumn, StatusColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

export default function InstalledItemsTable({
  stockItem
}: Readonly<{
  stockItem: any;
}>) {
  const table = useTable('stock_item_install');
  const user = useUserState();

  const installItemFields = useStockItemInstallFields({
    stockItem: stockItem
  });

  const installItem = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.stock_install),
    pk: stockItem.pk,
    title: t`Install Item`,
    table: table,
    successMessage: t`Item installed`,
    fields: installItemFields
  });

  const [selectedRecord, setSelectedRecord] = useState<any>({});

  const uninstallItemFields = useStockItemUninstallFields();

  const uninstallItem = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.stock_uninstall),
    pk: selectedRecord.pk,
    title: t`Uninstall Item`,
    table: table,
    successMessage: t`Item uninstalled`,
    fields: uninstallItemFields,
    initialData: {
      location: stockItem.location ?? stockItem.part_detail?.default_location
    }
  });

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        switchable: false,
        render: (record: any) => PartColumn({ part: record?.part_detail })
      },
      {
        accessor: 'quantity',
        switchable: false,
        render: (record: any) => {
          let text = record.quantity;

          if (record.serial && record.quantity == 1) {
            text = `# ${record.serial}`;
          }

          return text;
        }
      },
      {
        accessor: 'batch',
        switchable: false
      },
      StatusColumn({ model: ModelType.stockitem })
    ];
  }, []);

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='install'
        tooltip={t`Install Item`}
        onClick={() => {
          installItem.open();
        }}
        hidden={
          !user.hasChangeRole(UserRoles.stock) ||
          stockItem.is_building ||
          stockItem.part_detail?.assembly != true
        }
      />
    ];
  }, [stockItem, user]);

  const rowActions = useCallback(
    (record: any) => {
      return [
        {
          title: t`Uninstall`,
          tooltip: t`Uninstall stock item`,
          onClick: () => {
            setSelectedRecord(record);
            uninstallItem.open();
          },
          icon: <IconUnlink />,
          hidden: !user.hasChangeRole(UserRoles.stock)
        }
      ];
    },
    [user]
  );

  return (
    <>
      {installItem.modal}
      {uninstallItem.modal}
      {stockItem.pk ? (
        <InvenTreeTable
          url={apiUrl(ApiEndpoints.stock_item_list)}
          tableState={table}
          columns={tableColumns}
          props={{
            tableActions: tableActions,
            rowActions: rowActions,
            modelType: ModelType.stockitem,
            params: {
              belongs_to: stockItem.pk,
              part_detail: true
            }
          }}
        />
      ) : (
        <Skeleton />
      )}
    </>
  );
}
