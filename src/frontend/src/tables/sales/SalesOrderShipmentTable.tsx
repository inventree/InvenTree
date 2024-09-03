import { t } from '@lingui/macro';
import { IconTruckDelivery } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { useSalesOrderShipmentFields } from '../../forms/SalesOrderForms';
import { notYetImplemented } from '../../functions/notifications';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { DateColumn, LinkColumn, NoteColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

export default function SalesOrderShipmentTable({
  orderId
}: {
  orderId: number;
}) {
  const user = useUserState();
  const table = useTable('sales-order-shipment');

  const [selectedShipment, setSelectedShipment] = useState<number>(0);

  const newShipmentFields = useSalesOrderShipmentFields();
  const editShipmentFields = useSalesOrderShipmentFields();

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
    pk: selectedShipment,
    title: t`Delete Shipment`,
    table: table
  });

  const editShipment = useEditApiFormModal({
    url: ApiEndpoints.sales_order_shipment_list,
    pk: selectedShipment,
    fields: editShipmentFields,
    title: t`Edit Shipment`,
    table: table
  });

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'reference',
        title: t`Shipment Reference`,
        switchable: false
      },
      {
        accessor: 'allocations',
        title: t`Items`,
        render: (record: any) => {
          let allocations = record?.allocations ?? [];
          return allocations.length;
        }
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
      }),
      NoteColumn({
        accessor: 'notes'
      })
    ];
  }, []);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const shipped: boolean = !!record.shipment_date;

      return [
        {
          hidden: shipped || !user.hasChangeRole(UserRoles.sales_order),
          title: t`Complete Shipment`,
          icon: <IconTruckDelivery />,
          onClick: notYetImplemented
        },
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.sales_order),
          onClick: () => {
            setSelectedShipment(record.pk);
            editShipment.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.sales_order),
          onClick: () => {
            setSelectedShipment(record.pk);
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
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.sales_order_shipment_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          tableActions: tableActions,
          tableFilters: tableFilters,
          rowActions: rowActions,
          params: {
            order: orderId
          }
        }}
      />
    </>
  );
}
