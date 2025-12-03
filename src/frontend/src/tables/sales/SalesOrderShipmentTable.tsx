import { t } from '@lingui/core/macro';
import {
  IconCircleCheck,
  IconCircleX,
  IconTruckDelivery
} from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowCancelAction,
  RowEditAction,
  RowViewAction
} from '@lib/components/RowActions';
import { YesNoButton } from '@lib/components/YesNoButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import dayjs from 'dayjs';
import {
  useCheckShipmentForm,
  useSalesOrderShipmentCompleteFields,
  useSalesOrderShipmentFields,
  useUncheckShipmentForm
} from '../../forms/SalesOrderForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  CompanyColumn,
  DateColumn,
  LinkColumn,
  StatusColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

export default function SalesOrderShipmentTable({
  showOrderInfo = false,
  tableName,
  customerId,
  orderId,
  filters
}: Readonly<{
  showOrderInfo?: boolean;
  tableName?: string;
  customerId?: number;
  orderId?: number;
  filters?: any;
}>) {
  const user = useUserState();
  const navigate = useNavigate();
  const table = useTable(tableName ?? 'sales-order-shipment');

  const [selectedShipment, setSelectedShipment] = useState<any>({});

  const newShipmentFields = useSalesOrderShipmentFields({
    customerId: customerId
  });

  const editShipmentFields = useSalesOrderShipmentFields({
    customerId: customerId,
    pending: !selectedShipment.shipment_date
  });

  const completeShipmentFields = useSalesOrderShipmentCompleteFields({});

  const newShipment = useCreateApiFormModal({
    url: ApiEndpoints.sales_order_shipment_list,
    fields: newShipmentFields,
    title: t`Create Shipment`,
    table: table,
    initialData: {
      order: orderId
    }
  });

  const deleteShipment = useDeleteApiFormModal({
    url: ApiEndpoints.sales_order_shipment_list,
    pk: selectedShipment.pk,
    title: t`Cancel Shipment`,
    table: table
  });

  const editShipment = useEditApiFormModal({
    url: ApiEndpoints.sales_order_shipment_list,
    pk: selectedShipment.pk,
    fields: editShipmentFields,
    title: t`Edit Shipment`,
    table: table
  });

  const checkShipment = useCheckShipmentForm({
    shipmentId: selectedShipment.pk,
    onSuccess: () => {
      table.refreshTable();
    }
  });

  const uncheckShipment = useUncheckShipmentForm({
    shipmentId: selectedShipment.pk,
    onSuccess: () => {
      table.refreshTable();
    }
  });

  const completeShipment = useCreateApiFormModal({
    url: ApiEndpoints.sales_order_shipment_complete,
    pk: selectedShipment.pk,
    fields: completeShipmentFields,
    title: t`Complete Shipment`,
    table: table,
    focus: 'tracking_number',
    initialData: {
      ...selectedShipment,
      shipment_date: dayjs().format('YYYY-MM-DD')
    }
  });

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'customer',
        title: t`Customer`,
        switchable: true,
        sortable: true,
        hidden: !showOrderInfo,
        render: (record: any) => (
          <CompanyColumn company={record.customer_detail} />
        )
      },
      {
        switchable: false,
        accessor: 'order_detail.reference',
        title: t`Sales Order`,
        hidden: !showOrderInfo,
        sortable: false
      },
      StatusColumn({
        switchable: true,
        model: ModelType.salesorder,
        accessor: 'order_detail.status',
        title: t`Order Status`,
        hidden: !showOrderInfo
      }),
      {
        accessor: 'reference',
        title: t`Shipment Reference`,
        switchable: false,
        sortable: true
      },
      {
        accessor: 'allocated_items',
        sortable: true,
        switchable: false,
        title: t`Items`
      },
      {
        accessor: 'checked',
        title: t`Checked`,
        switchable: true,
        sortable: false,
        render: (record: any) => <YesNoButton value={!!record.checked_by} />
      },
      {
        accessor: 'shipped',
        title: t`Shipped`,
        switchable: true,
        sortable: false,
        render: (record: any) => <YesNoButton value={!!record.shipment_date} />
      },
      {
        accessor: 'delivered',
        title: t`Delivered`,
        switchable: true,
        sortable: false,
        render: (record: any) => <YesNoButton value={!!record.delivery_date} />
      },
      DateColumn({
        accessor: 'shipment_date',
        title: t`Shipment Date`
      }),
      DateColumn({
        accessor: 'delivery_date',
        title: t`Delivery Date`
      }),
      {
        accessor: 'tracking_number'
      },
      {
        accessor: 'invoice_number'
      },
      LinkColumn({
        accessor: 'link'
      })
    ];
  }, [showOrderInfo]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const shipped: boolean = !!record.shipment_date;

      return [
        {
          hidden:
            !!record.checked_by || !user.hasChangeRole(UserRoles.sales_order),
          title: t`Check Shipment`,
          color: 'blue',
          icon: <IconCircleCheck />,
          onClick: () => {
            setSelectedShipment(record);
            checkShipment.open();
          }
        },
        {
          hidden:
            shipped ||
            !record.checked_by ||
            !user.hasChangeRole(UserRoles.sales_order),
          title: t`Uncheck Shipment`,
          color: 'red',
          icon: <IconCircleX />,
          onClick: () => {
            setSelectedShipment(record);
            uncheckShipment.open();
          }
        },
        {
          hidden: shipped || !user.hasChangeRole(UserRoles.sales_order),
          title: t`Complete Shipment`,
          color: 'green',
          icon: <IconTruckDelivery />,
          onClick: () => {
            setSelectedShipment(record);
            completeShipment.open();
          }
        },
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.sales_order),
          tooltip: t`Edit shipment`,
          onClick: () => {
            setSelectedShipment(record);
            editShipment.open();
          }
        }),
        RowCancelAction({
          hidden: shipped || !user.hasDeleteRole(UserRoles.sales_order),
          tooltip: t`Cancel shipment`,
          onClick: () => {
            setSelectedShipment(record);
            deleteShipment.open();
          }
        }),
        RowViewAction({
          title: t`View Sales Order`,
          modelType: ModelType.salesorder,
          modelId: record.order,
          hidden:
            !record.order ||
            !showOrderInfo ||
            !user.hasViewRole(UserRoles.sales_order),
          navigate: navigate
        })
      ];
    },
    [showOrderInfo, user]
  );

  const tableActions = useMemo(() => {
    // No actions possible if no order is specified
    if (!orderId) {
      return [];
    }

    return [
      <AddItemButton
        key='add-shipment'
        tooltip={t`Add shipment`}
        hidden={!user.hasAddRole(UserRoles.sales_order)}
        onClick={() => {
          newShipment.open();
        }}
      />
    ];
  }, [orderId, user]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'checked',
        label: t`Checked`,
        description: t`Show shipments which have been checked`
      },
      {
        name: 'shipped',
        label: t`Shipped`,
        description: t`Show shipments which have been shipped`
      },
      {
        name: 'delivered',
        label: t`Delivered`,
        description: t`Show shipments which have been delivered`
      }
    ];
  }, []);

  return (
    <>
      {newShipment.modal}
      {editShipment.modal}
      {checkShipment.modal}
      {deleteShipment.modal}
      {uncheckShipment.modal}
      {completeShipment.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.sales_order_shipment_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          tableActions: tableActions,
          tableFilters: tableFilters,
          modelType: ModelType.salesordershipment,
          enableSelection: true,
          enableReports: true,
          rowActions: rowActions,
          params: {
            order: orderId,
            order_detail: true,
            customer_detail: showOrderInfo,
            ...filters
          }
        }}
      />
    </>
  );
}
