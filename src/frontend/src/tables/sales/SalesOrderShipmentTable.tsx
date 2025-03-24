import { t } from '@lingui/macro';
import { IconTruckDelivery } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { YesNoButton } from '@lib/components';
import { AddItemButton } from '@lib/components/buttons/AddItemButton';
import { ApiEndpoints } from '@lib/core';
import { ModelType } from '@lib/core';
import { UserRoles } from '@lib/core';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '@lib/forms';
import { apiUrl } from '@lib/functions';
import { useTable } from '@lib/hooks';
import { useUserState } from '@lib/states';
import type { RowAction, TableColumn } from '@lib/tables';
import type { TableFilter } from '@lib/tables';
import { RowCancelAction, RowEditAction, RowViewAction } from '@lib/tables';
import dayjs from 'dayjs';
import { InvenTreeTable } from '../../../lib/tables/InvenTreeTable';
import {
  useSalesOrderShipmentCompleteFields,
  useSalesOrderShipmentFields
} from '../../forms/SalesOrderForms';
import { DateColumn, LinkColumn } from '../ColumnRenderers';

export default function SalesOrderShipmentTable({
  orderId
}: Readonly<{
  orderId: number;
}>) {
  const user = useUserState();
  const navigate = useNavigate();
  const table = useTable('sales-order-shipment');

  const [selectedShipment, setSelectedShipment] = useState<any>({});

  const newShipmentFields = useSalesOrderShipmentFields({});

  const editShipmentFields = useSalesOrderShipmentFields({});

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
        accessor: 'shipped',
        title: t`Shipped`,
        switchable: true,
        sortable: false,
        render: (record: any) => <YesNoButton value={!!record.shipment_date} />
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
  }, []);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const shipped: boolean = !!record.shipment_date;

      return [
        RowViewAction({
          title: t`View Shipment`,
          modelType: ModelType.salesordershipment,
          modelId: record.pk,
          navigate: navigate
        }),
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
        })
      ];
    },
    [user]
  );

  const tableActions = useMemo(() => {
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
  }, [user]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
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
      {deleteShipment.modal}
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
            order: orderId
          }
        }}
      />
    </>
  );
}
