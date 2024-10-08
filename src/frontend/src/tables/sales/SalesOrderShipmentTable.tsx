import { t } from '@lingui/macro';
import { IconArrowRight, IconTruckDelivery } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useSalesOrderShipmentFields } from '../../forms/SalesOrderForms';
import { navigateToLink } from '../../functions/navigation';
import { notYetImplemented } from '../../functions/notifications';
import { getDetailUrl } from '../../functions/urls';
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
import { RowAction, RowCancelAction, RowEditAction } from '../RowActions';

export default function SalesOrderShipmentTable({
  orderId
}: Readonly<{
  orderId: number;
}>) {
  const user = useUserState();
  const navigate = useNavigate();
  const table = useTable('sales-order-shipment');

  const [selectedShipment, setSelectedShipment] = useState<number>(0);

  const newShipmentFields = useSalesOrderShipmentFields({});

  const editShipmentFields = useSalesOrderShipmentFields({});

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
    title: t`Cancel Shipment`,
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
        switchable: false,
        sortable: true
      },
      {
        accessor: 'allocated_items',
        sortable: true,
        switchable: false,
        title: t`Items`
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
        {
          title: t`View Shipment`,
          icon: <IconArrowRight />,
          onClick: (event: any) => {
            navigateToLink(
              getDetailUrl(ModelType.salesordershipment, record.pk),
              navigate,
              event
            );
          }
        },
        {
          hidden: shipped || !user.hasChangeRole(UserRoles.sales_order),
          title: t`Complete Shipment`,
          color: 'green',
          icon: <IconTruckDelivery />,
          onClick: notYetImplemented
        },
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.sales_order),
          tooltip: t`Edit shipment`,
          onClick: () => {
            setSelectedShipment(record.pk);
            editShipment.open();
          }
        }),
        RowCancelAction({
          hidden: shipped || !user.hasDeleteRole(UserRoles.sales_order),
          tooltip: t`Cancel shipment`,
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
        key="add-shipment"
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
