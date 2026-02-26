import { t } from '@lingui/core/macro';
import { Grid, Skeleton, Stack, Text } from '@mantine/core';
import {
  IconBookmark,
  IconCircleCheck,
  IconCircleX,
  IconInfoCircle
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { getDetailUrl } from '@lib/functions/Navigation';
import dayjs from 'dayjs';
import PrimaryActionButton from '../../components/buttons/PrimaryActionButton';
import { PrintingActions } from '../../components/buttons/PrintingActions';
import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import DetailsBadge from '../../components/details/DetailsBadge';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import {
  BarcodeActionDropdown,
  CancelItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import AttachmentPanel from '../../components/panels/AttachmentPanel';
import NotesPanel from '../../components/panels/NotesPanel';
import type { PanelType } from '../../components/panels/Panel';
import { PanelGroup } from '../../components/panels/PanelGroup';
import { RenderAddress } from '../../components/render/Company';
import { RenderUser } from '../../components/render/User';
import { formatDate } from '../../defaults/formatters';
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
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';
import SalesOrderAllocationTable from '../../tables/sales/SalesOrderAllocationTable';

export default function SalesOrderShipmentDetail() {
  const { id } = useParams();
  const user = useUserState();
  const navigate = useNavigate();

  const userId = useMemo(() => user.userId(), [user]);

  const {
    instance: shipment,
    instanceQuery: shipmentQuery,
    refreshInstance: refreshShipment
  } = useInstance({
    endpoint: ApiEndpoints.sales_order_shipment_list,
    pk: id,
    params: {
      order_detail: true
    }
  });

  const { instance: customer, instanceQuery: customerQuery } = useInstance({
    endpoint: ApiEndpoints.company_list,
    pk: shipment.order_detail?.customer,
    hasPrimaryKey: true
  });

  const isPending = useMemo(() => !shipment.shipment_date, [shipment]);

  const isChecked = useMemo(() => !!shipment.checked_by, [shipment]);

  const detailsPanel = useMemo(() => {
    if (shipmentQuery.isFetching || customerQuery.isFetching) {
      return <Skeleton />;
    }

    const data: any = {
      ...shipment,
      customer: customer?.pk,
      customer_name: customer?.name,
      customer_reference: shipment.order_detail?.customer_reference
    };

    // Top Left: Order / customer information
    const tl: DetailsField[] = [
      {
        type: 'link',
        model: ModelType.salesorder,
        name: 'order',
        label: t`Sales Order`,
        icon: 'sales_orders',
        model_field: 'reference'
      },
      {
        type: 'link',
        name: 'customer',
        icon: 'customers',
        label: t`Customer`,
        model: ModelType.company,
        model_field: 'name',
        hidden: !data.customer
      },
      {
        type: 'link',
        external: true,
        name: 'link',
        label: t`Link`,
        copy: true,
        hidden: !shipment.link
      }
    ];

    // Top right: Shipment information
    const tr: DetailsField[] = [
      {
        type: 'text',
        name: 'customer_reference',
        icon: 'serial',
        label: t`Customer Reference`,
        hidden: !data.customer_reference,
        copy: true
      },
      {
        type: 'text',
        name: 'reference',
        icon: 'serial',
        label: t`Shipment Reference`,
        copy: true
      },
      {
        type: 'text',
        name: 'tracking_number',
        label: t`Tracking Number`,
        icon: 'trackable',
        value_formatter: () => shipment.tracking_number || '---',
        copy: !!shipment.tracking_number
      },
      {
        type: 'text',
        name: 'invoice_number',
        label: t`Invoice Number`,
        icon: 'serial',
        value_formatter: () => shipment.invoice_number || '---',
        copy: !!shipment.invoice_number
      }
    ];

    const address: any =
      shipment.shipment_address_detail || shipment.order_detail?.address_detail;

    const bl: DetailsField[] = [
      {
        type: 'text',
        name: 'address',
        label: t`Shipping Address`,
        icon: 'address',
        value_formatter: () =>
          address ? (
            <RenderAddress
              instance={
                shipment.shipment_address_detail ||
                shipment.order_detail?.address_detail
              }
            />
          ) : (
            <Text size='sm' c='red'>{t`Not specified`}</Text>
          )
      }
    ];

    const br: DetailsField[] = [
      {
        type: 'text',
        name: 'allocated_items',
        icon: 'packages',
        label: t`Allocated Items`
      },
      {
        type: 'text',
        name: 'checked_by',
        label: t`Checked By`,
        icon: 'check',
        value_formatter: () =>
          shipment.checked_by_detail ? (
            <RenderUser instance={shipment.checked_by_detail} />
          ) : (
            <Text size='sm' c='red'>{t`Not checked`}</Text>
          )
      },
      {
        type: 'text',
        name: 'shipment_date',
        label: t`Shipment Date`,
        icon: 'calendar',
        value_formatter: () => formatDate(shipment.shipment_date),
        hidden: !shipment.shipment_date
      },
      {
        type: 'text',
        name: 'delivery_date',
        label: t`Delivery Date`,
        icon: 'calendar',
        value_formatter: () => formatDate(shipment.delivery_date),
        hidden: !shipment.delivery_date
      }
    ];

    return (
      <>
        <ItemDetailsGrid>
          <Grid grow>
            <DetailsImage
              appRole={UserRoles.sales_order}
              apiPath={ApiEndpoints.company_list}
              src={customer?.image}
              pk={customer?.pk}
              imageActions={{
                selectExisting: false,
                downloadImage: false,
                uploadFile: false,
                deleteFile: false
              }}
            />
            <Grid.Col span={{ base: 12, sm: 8 }}>
              <DetailsTable fields={tl} item={data} />
            </Grid.Col>
          </Grid>
          <DetailsTable fields={tr} item={data} />
          <DetailsTable fields={bl} item={data} />
          <DetailsTable fields={br} item={data} />
        </ItemDetailsGrid>
      </>
    );
  }, [shipment, shipmentQuery, customer, customerQuery]);

  const shipmentPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'detail',
        label: t`Shipment Details`,
        icon: <IconInfoCircle />,
        content: detailsPanel
      },
      {
        name: 'items',
        label: t`Allocated Stock`,
        icon: <IconBookmark />,
        content: (
          <SalesOrderAllocationTable
            orderId={shipment.order}
            shipmentId={shipment.pk}
            showPartInfo
            allowEdit={isPending}
            modelField='item'
            modelTarget={ModelType.stockitem}
          />
        )
      },
      AttachmentPanel({
        model_type: ModelType.salesordershipment,
        model_id: shipment.pk
      }),
      NotesPanel({
        model_type: ModelType.salesordershipment,
        model_id: shipment.pk,
        has_note: !!shipment.notes
      })
    ];
  }, [isPending, shipment, detailsPanel]);

  const editShipmentFields = useSalesOrderShipmentFields({
    pending: isPending,
    customerId: shipment.order_detail?.customer
  });

  const editShipment = useEditApiFormModal({
    url: ApiEndpoints.sales_order_shipment_list,
    pk: shipment.pk,
    fields: editShipmentFields,
    title: t`Edit Shipment`,
    onFormSuccess: refreshShipment
  });

  const deleteShipment = useDeleteApiFormModal({
    url: ApiEndpoints.sales_order_shipment_list,
    pk: shipment.pk,
    title: t`Cancel Shipment`,
    onFormSuccess: () => {
      // Shipment has been deleted - navigate back to the sales order
      navigate(getDetailUrl(ModelType.salesorder, shipment.order));
    }
  });

  const completeShipmentFields = useSalesOrderShipmentCompleteFields({});

  const completeShipment = useCreateApiFormModal({
    url: ApiEndpoints.sales_order_shipment_complete,
    pk: shipment.pk,
    fields: completeShipmentFields,
    title: t`Complete Shipment`,
    focus: 'tracking_number',
    initialData: {
      ...shipment,
      shipment_date: dayjs().format('YYYY-MM-DD')
    },
    onFormSuccess: refreshShipment
  });

  const checkShipment = useCheckShipmentForm({
    shipmentId: shipment.pk,
    onSuccess: refreshShipment
  });

  const uncheckShipment = useUncheckShipmentForm({
    shipmentId: shipment.pk,
    onSuccess: refreshShipment
  });

  const shipmentBadges = useMemo(() => {
    if (shipmentQuery.isFetching) {
      return [];
    }

    return [
      <DetailsBadge
        key='pending'
        label={t`Pending`}
        color='gray'
        visible={isPending}
      />,
      <DetailsBadge
        key='checked'
        label={t`Checked`}
        color='green'
        visible={isPending && isChecked}
      />,
      <DetailsBadge
        key='not-checked'
        label={t`Not Checked`}
        color='red'
        visible={isPending && !isChecked}
      />,
      <DetailsBadge
        key='shipped'
        label={t`Shipped`}
        color='green'
        visible={!isPending}
      />,
      <DetailsBadge
        key='delivered'
        label={t`Delivered`}
        color='blue'
        visible={!!shipment.delivery_date}
      />
    ];
  }, [isPending, isChecked, shipment.deliveryDate, shipmentQuery.isFetching]);

  const shipmentActions = useMemo(() => {
    const canEdit: boolean = user.hasChangePermission(
      ModelType.salesordershipment
    );

    return [
      <PrimaryActionButton
        key='send-shipment'
        title={t`Send Shipment`}
        icon='sales_orders'
        hidden={!isPending}
        color='green'
        onClick={() => {
          completeShipment.open();
        }}
      />,
      <BarcodeActionDropdown
        key='barcode'
        model={ModelType.salesordershipment}
        pk={shipment.pk}
        hash={shipment?.barcode_hash}
      />,
      <PrintingActions
        key='print'
        modelType={ModelType.salesordershipment}
        items={[shipment.pk]}
        enableLabels
        enableReports
      />,
      <OptionsActionDropdown
        key='actions'
        tooltip={t`Shipment Actions`}
        actions={[
          EditItemAction({
            hidden: !canEdit,
            onClick: editShipment.open,
            tooltip: t`Edit Shipment`
          }),
          {
            hidden: !isPending || isChecked,
            name: t`Check`,
            tooltip: t`Mark shipment as checked`,
            icon: <IconCircleCheck color='green' />,
            onClick: checkShipment.open
          },
          {
            hidden: !isPending || !isChecked,
            name: t`Uncheck`,
            tooltip: t`Mark shipment as unchecked`,
            icon: <IconCircleX color='red' />,
            onClick: uncheckShipment.open
          },
          CancelItemAction({
            hidden: !isPending,
            onClick: deleteShipment.open,
            tooltip: t`Cancel Shipment`
          })
        ]}
      />
    ];
  }, [isChecked, isPending, user, shipment]);

  return (
    <>
      {completeShipment.modal}
      {editShipment.modal}
      {deleteShipment.modal}
      {checkShipment.modal}
      {uncheckShipment.modal}
      <InstanceDetail
        query={shipmentQuery}
        requiredRole={UserRoles.sales_order}
      >
        <Stack gap='xs'>
          <PageDetail
            title={`${t`Sales Order Shipment`}: ${shipment.reference}`}
            subtitle={`${t`Sales Order`}: ${shipment.order_detail?.reference}`}
            breadcrumbs={[
              { name: t`Sales`, url: '/sales/' },
              {
                name: shipment.order_detail?.reference,
                url: getDetailUrl(ModelType.salesorder, shipment.order)
              }
            ]}
            badges={shipmentBadges}
            imageUrl={customer?.image}
            editAction={editShipment.open}
            editEnabled={user.hasChangePermission(ModelType.salesordershipment)}
            actions={shipmentActions}
          />
          <PanelGroup
            pageKey='salesordershipment'
            panels={shipmentPanels}
            model={ModelType.salesordershipment}
            reloadInstance={refreshShipment}
            instance={shipment}
            id={shipment.pk}
          />
        </Stack>
      </InstanceDetail>
    </>
  );
}
