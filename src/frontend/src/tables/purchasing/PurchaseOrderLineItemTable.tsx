import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { IconFileArrowLeft, IconSquareArrowRight } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { ActionButton } from '../../components/buttons/ActionButton';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import ImporterDrawer from '../../components/importer/ImporterDrawer';
import { ProgressBar } from '../../components/items/ProgressBar';
import { RenderStockLocation } from '../../components/render/Stock';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { dataImporterSessionFields } from '../../forms/ImporterForms';
import {
  usePurchaseOrderLineItemFields,
  useReceiveLineItems
} from '../../forms/PurchaseOrderForms';
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
import {
  CurrencyColumn,
  LinkColumn,
  NoteColumn,
  PartColumn,
  ReferenceColumn,
  TargetDateColumn,
  TotalPriceColumn
} from '../ColumnRenderers';
import type { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import {
  type RowAction,
  RowDeleteAction,
  RowDuplicateAction,
  RowEditAction
} from '../RowActions';
import { TableHoverCard } from '../TableHoverCard';

/*
 * Display a table of purchase order line items, for a specific order
 */
export function PurchaseOrderLineItemTable({
  order,
  orderId,
  currency,
  supplierId,
  params
}: Readonly<{
  order: any;
  orderId: number;
  currency: string;
  supplierId?: number;
  params?: any;
}>) {
  const table = useTable('purchase-order-line-item');

  const user = useUserState();

  // Data import
  const [importOpened, setImportOpened] = useState<boolean>(false);
  const [selectedSession, setSelectedSession] = useState<number | undefined>(
    undefined
  );

  const importSessionFields = useMemo(() => {
    const fields = dataImporterSessionFields();

    fields.model_type.hidden = true;
    fields.model_type.value = ModelType.purchaseorderlineitem;

    // Specify override values for import
    fields.field_overrides.value = {
      order: orderId
    };

    // Specify default values based on the order data
    fields.field_defaults.value = {
      purchase_price_currency:
        order?.order_currency || order?.supplier_detail?.currency || undefined
    };

    fields.field_filters.value = {
      part: {
        supplier: supplierId,
        active: true
      }
    };

    return fields;
  }, [order, orderId, supplierId]);

  const importLineItems = useCreateApiFormModal({
    url: ApiEndpoints.import_session_list,
    title: t`Import Line Items`,
    fields: importSessionFields,
    onFormSuccess: (response: any) => {
      setSelectedSession(response.pk);
      setImportOpened(true);
    }
  });

  const [singleRecord, setSingleRecord] = useState(null);

  const receiveLineItems = useReceiveLineItems({
    items: singleRecord ? [singleRecord] : table.selectedRecords,
    orderPk: orderId,
    destinationPk: order.destination,
    formProps: {
      // Timeout is a small hack to prevent function being called before re-render
      onClose: () => {
        table.refreshTable();
        setTimeout(() => setSingleRecord(null), 500);
      }
    }
  });

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        title: t`Part`,
        sortable: true,
        ordering: 'part_name',
        switchable: false,
        render: (record: any) => PartColumn({ part: record.part_detail })
      },
      {
        accessor: 'part_detail.IPN',
        sortable: true,
        ordering: 'IPN'
      },
      {
        accessor: 'part_detail.description',
        sortable: false
      },
      ReferenceColumn({}),
      {
        accessor: 'quantity',
        title: t`Quantity`,
        sortable: true,
        switchable: false,
        render: (record: any) => {
          const supplier_part = record?.supplier_part_detail ?? {};
          const part = record?.part_detail ?? supplier_part?.part_detail ?? {};
          const extra = [];

          if (
            supplier_part?.pack_quantity_native != undefined &&
            supplier_part.pack_quantity_native != 1
          ) {
            const total = record.quantity * supplier_part.pack_quantity_native;

            extra.push(
              <Text key='pack-quantity'>
                {t`Pack Quantity`}: {supplier_part.pack_quantity}
              </Text>
            );

            extra.push(
              <Text key='total-quantity'>
                {t`Total Quantity`}: {total} {part?.units}
              </Text>
            );
          }

          return (
            <TableHoverCard
              value={record.quantity}
              extra={extra}
              title={t`Quantity`}
            />
          );
        }
      },
      {
        accessor: 'received',
        title: t`Received`,
        sortable: false,

        render: (record: any) => (
          <ProgressBar
            progressLabel={true}
            value={record.received}
            maximum={record.quantity}
          />
        )
      },
      {
        accessor: 'supplier_part_detail.packaging',
        sortable: false,
        title: t`Packaging`
      },
      {
        accessor: 'supplier_part_detail.pack_quantity',
        sortable: false,
        title: t`Pack Quantity`
      },
      {
        accessor: 'sku',
        title: t`Supplier Code`,
        switchable: false,
        sortable: true,
        ordering: 'SKU'
      },
      LinkColumn({
        accessor: 'supplier_part_detail.link',
        title: t`Supplier Link`,
        sortable: false
      }),
      {
        accessor: 'mpn',
        ordering: 'MPN',
        title: t`Manufacturer Code`,
        sortable: true
      },
      CurrencyColumn({
        accessor: 'purchase_price',
        title: t`Unit Price`
      }),
      TotalPriceColumn(),
      TargetDateColumn({}),
      {
        accessor: 'destination',
        title: t`Destination`,
        sortable: false,
        render: (record: any) =>
          record.destination
            ? RenderStockLocation({ instance: record.destination_detail })
            : '-'
      },
      NoteColumn({}),
      LinkColumn({})
    ];
  }, [orderId, user]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'received',
        label: t`Received`,
        description: t`Show line items which have been received`
      }
    ];
  }, []);

  const addPurchaseOrderFields = usePurchaseOrderLineItemFields({
    create: true,
    orderId: orderId,
    supplierId: supplierId
  });

  const [initialData, setInitialData] = useState<any>({});

  const newLine = useCreateApiFormModal({
    url: ApiEndpoints.purchase_order_line_list,
    title: t`Add Line Item`,
    fields: addPurchaseOrderFields,
    initialData: {
      ...initialData,
      purchase_price_currency: currency
    },
    table: table
  });

  const [selectedLine, setSelectedLine] = useState<number>(0);

  const editPurchaseOrderFields = usePurchaseOrderLineItemFields({
    create: false,
    orderId: orderId,
    supplierId: supplierId
  });

  const editLine = useEditApiFormModal({
    url: ApiEndpoints.purchase_order_line_list,
    pk: selectedLine,
    title: t`Edit Line Item`,
    fields: editPurchaseOrderFields,
    table: table
  });

  const deleteLine = useDeleteApiFormModal({
    url: ApiEndpoints.purchase_order_line_list,
    pk: selectedLine,
    title: t`Delete Line Item`,
    table: table
  });

  const poStatus = useStatusCodes({ modelType: ModelType.purchaseorder });

  const orderOpen: boolean = useMemo(() => {
    return (
      order.status == poStatus.PENDING ||
      order.status == poStatus.PLACED ||
      order.status == poStatus.ON_HOLD
    );
  }, [order, poStatus]);

  const orderPlaced: boolean = useMemo(() => {
    return order.status == poStatus.PLACED;
  }, [order, poStatus]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const received = (record?.received ?? 0) >= (record?.quantity ?? 0);

      return [
        {
          hidden: received || !orderOpen,
          title: t`Receive line item`,
          icon: <IconSquareArrowRight />,
          color: 'green',
          onClick: () => {
            setSingleRecord(record);
            receiveLineItems.open();
          }
        },
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.purchase_order),
          onClick: () => {
            setSelectedLine(record.pk);
            editLine.open();
          }
        }),
        RowDuplicateAction({
          hidden: !orderOpen || !user.hasAddRole(UserRoles.purchase_order),
          onClick: () => {
            setInitialData({ ...record });
            newLine.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.purchase_order),
          onClick: () => {
            setSelectedLine(record.pk);
            deleteLine.open();
          }
        })
      ];
    },
    [orderId, user, orderOpen]
  );

  // Custom table actions
  const tableActions = useMemo(() => {
    return [
      <ActionButton
        key='import-line-items'
        hidden={!orderOpen || !user.hasAddRole(UserRoles.purchase_order)}
        tooltip={t`Import Line Items`}
        icon={<IconFileArrowLeft />}
        onClick={() => importLineItems.open()}
      />,
      <AddItemButton
        key='add-line-item'
        tooltip={t`Add Line Item`}
        onClick={() => {
          setInitialData({
            order: orderId
          });
          newLine.open();
        }}
        hidden={!orderOpen || !user?.hasAddRole(UserRoles.purchase_order)}
      />,
      <ActionButton
        key='receive-items'
        text={t`Receive items`}
        icon={<IconSquareArrowRight />}
        onClick={() => receiveLineItems.open()}
        disabled={table.selectedRecords.length === 0}
        hidden={!orderPlaced || !user.hasChangeRole(UserRoles.purchase_order)}
      />
    ];
  }, [orderId, user, table, orderOpen, orderPlaced]);

  return (
    <>
      {importLineItems.modal}
      {receiveLineItems.modal}
      {newLine.modal}
      {editLine.modal}
      {deleteLine.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.purchase_order_line_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableSelection: true,
          enableDownload: true,
          params: {
            ...params,
            order: orderId,
            part_detail: true
          },
          rowActions: rowActions,
          tableActions: tableActions,
          tableFilters: tableFilters,
          modelType: ModelType.supplierpart,
          modelField: 'part'
        }}
      />
      <ImporterDrawer
        sessionId={selectedSession ?? -1}
        opened={selectedSession != undefined && importOpened}
        onClose={() => {
          setSelectedSession(undefined);
          setImportOpened(false);
          table.refreshTable();
        }}
      />
    </>
  );
}
