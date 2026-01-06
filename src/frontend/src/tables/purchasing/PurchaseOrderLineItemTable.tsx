import { t } from '@lingui/core/macro';
import { Text } from '@mantine/core';
import { IconFileArrowLeft, IconSquareArrowRight } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { ActionButton } from '@lib/components/ActionButton';
import { AddItemButton } from '@lib/components/AddItemButton';
import { ProgressBar } from '@lib/components/ProgressBar';
import {
  type RowAction,
  RowDeleteAction,
  RowDuplicateAction,
  RowEditAction,
  RowViewAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { formatDecimal } from '@lib/functions/Formatting';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { useNavigate } from 'react-router-dom';
import ImporterDrawer from '../../components/importer/ImporterDrawer';
import { RenderInstance } from '../../components/render/Instance';
import { formatCurrency } from '../../defaults/formatters';
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
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import {
  CurrencyColumn,
  DescriptionColumn,
  LinkColumn,
  LocationColumn,
  NoteColumn,
  PartColumn,
  ProjectCodeColumn,
  ReferenceColumn,
  TargetDateColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';

/*
 * Display a table of purchase order line items, for a specific order
 */
export function PurchaseOrderLineItemTable({
  order,
  orderDetailRefresh,
  orderId,
  currency,
  supplierId,
  editable,
  params
}: Readonly<{
  order: any;
  orderDetailRefresh: () => void;
  orderId: number;
  currency: string;
  supplierId?: number;
  editable: boolean;
  params?: any;
}>) {
  const table = useTable('purchase-order-line-item');

  const globalSettings = useGlobalSettingsState();
  const navigate = useNavigate();
  const user = useUserState();

  // Data import
  const [importOpened, setImportOpened] = useState<boolean>(false);
  const [selectedSession, setSelectedSession] = useState<number | undefined>(
    undefined
  );

  const importSessionFields = useMemo(() => {
    const fields = dataImporterSessionFields({
      modelType: ModelType.purchaseorderlineitem
    });

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
        table.clearSelectedRecords();
        table.refreshTable();
        setTimeout(() => setSingleRecord(null), 500);
      }
    }
  });

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      PartColumn({
        part: 'part_detail',
        ordering: 'part_name'
      }),
      {
        accessor: 'part_detail.IPN',
        sortable: true,
        ordering: 'IPN'
      },
      DescriptionColumn({
        accessor: 'part_detail.description'
      }),
      ReferenceColumn({}),
      ProjectCodeColumn({}),
      {
        accessor: 'build_order',
        title: t`Build Order`,
        sortable: true,
        defaultVisible: false,
        render: (record: any) => {
          if (record.build_order_detail) {
            return (
              <RenderInstance
                instance={record.build_order_detail}
                model={ModelType.build}
              />
            );
          } else {
            return '-';
          }
        }
      },
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
              <Text key='pack-quantity' size='sm'>
                {t`Pack Quantity`}: {supplier_part.pack_quantity}
              </Text>
            );

            extra.push(
              <Text key='total-quantity' size='sm'>
                {t`Total Quantity`}: {formatDecimal(total)} {part?.units}
              </Text>
            );
          }

          return (
            <TableHoverCard
              value={formatDecimal(record.quantity)}
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
        title: t`Packaging`,
        defaultVisible: false
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
        sortable: false,
        defaultVisible: false
      }),
      {
        accessor: 'mpn',
        ordering: 'MPN',
        title: t`Manufacturer Code`,
        sortable: true,
        defaultVisible: false
      },
      CurrencyColumn({
        accessor: 'purchase_price',
        title: t`Unit Price`
      }),
      {
        accessor: 'total_price',
        title: t`Total Price`,
        render: (record: any) =>
          formatCurrency(record.purchase_price, {
            currency: record.purchase_price_currency,
            multiplier: record.quantity
          })
      },
      TargetDateColumn({}),
      LocationColumn({
        accessor: 'destination_detail',
        sortable: false,
        title: t`Destination`
      }),
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
    supplierId: supplierId,
    currency: currency
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
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const [selectedLine, setSelectedLine] = useState<number>(0);

  const editLineItemFields = usePurchaseOrderLineItemFields({
    create: false,
    orderId: orderId,
    supplierId: supplierId,
    currency: currency
  });

  const editLine = useEditApiFormModal({
    url: ApiEndpoints.purchase_order_line_list,
    pk: selectedLine,
    title: t`Edit Line Item`,
    fields: editLineItemFields,
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const deleteLine = useDeleteApiFormModal({
    url: ApiEndpoints.purchase_order_line_list,
    pk: selectedLine,
    title: t`Delete Line Item`,
    onFormSuccess: orderDetailRefresh,
    table: table
  });

  const poStatus = useStatusCodes({ modelType: ModelType.purchaseorder });

  const orderPlaced: boolean = useMemo(() => {
    return order.status == poStatus.PLACED;
  }, [order, poStatus]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const received = (record?.received ?? 0) >= (record?.quantity ?? 0);

      const canEdit: boolean =
        editable && user.hasChangeRole(UserRoles.purchase_order);

      return [
        {
          hidden: received || !orderPlaced,
          title: t`Receive line item`,
          icon: <IconSquareArrowRight />,
          color: 'green',
          onClick: () => {
            setSingleRecord(record);
            receiveLineItems.open();
          }
        },
        RowEditAction({
          hidden: !canEdit,
          onClick: () => {
            setSelectedLine(record.pk);
            editLine.open();
          }
        }),
        RowDuplicateAction({
          hidden: !canEdit || !user.hasAddRole(UserRoles.purchase_order),
          onClick: () => {
            setInitialData({ ...record });
            newLine.open();
          }
        }),
        RowDeleteAction({
          hidden: !canEdit || !user.hasDeleteRole(UserRoles.purchase_order),
          onClick: () => {
            setSelectedLine(record.pk);
            deleteLine.open();
          }
        }),
        RowViewAction({
          hidden: !record.build_order,
          title: t`View Build Order`,
          modelType: ModelType.build,
          modelId: record.build_order,
          navigate: navigate
        })
      ];
    },
    [orderId, user, editable, orderPlaced]
  );

  // Custom table actions
  const tableActions = useMemo(() => {
    return [
      <ActionButton
        key='import-line-items'
        hidden={!editable || !user.hasAddRole(UserRoles.purchase_order)}
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
        hidden={!editable || !user?.hasAddRole(UserRoles.purchase_order)}
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
  }, [orderId, user, table, editable, orderPlaced]);

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
            part_detail: true,
            destination_detail: true
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
