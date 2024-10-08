import { t } from '@lingui/macro';
import { Grid, Skeleton, Stack } from '@mantine/core';
import { IconInfoCircle, IconPackages } from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import PrimaryActionButton from '../../components/buttons/PrimaryActionButton';
import { PrintingActions } from '../../components/buttons/PrintingActions';
import { DetailsField, DetailsTable } from '../../components/details/Details';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import {
  BarcodeActionDropdown,
  CancelItemAction,
  DeleteItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import AttachmentPanel from '../../components/panels/AttachmentPanel';
import NotesPanel from '../../components/panels/NotesPanel';
import { PanelType } from '../../components/panels/Panel';
import { PanelGroup } from '../../components/panels/PanelGroup';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { getDetailUrl } from '../../functions/urls';
import { useEditApiFormModal } from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';

export default function SalesOrderShipmentDetail() {
  const { id } = useParams();
  const user = useUserState();

  const {
    instance: shipment,
    instanceQuery: shipmentQuery,
    refreshInstance: refreshShipment,
    requestStatus: shipmentStatus
  } = useInstance({
    endpoint: ApiEndpoints.sales_order_shipment_list,
    pk: id,
    params: {
      order_detail: true
    }
  });

  const {
    instance: customer,
    instanceQuery: customerQuery,
    refreshInstance: refreshCustomer,
    requestStatus: customerStatus
  } = useInstance({
    endpoint: ApiEndpoints.company_list,
    pk: shipment.order_detail?.customer,
    hasPrimaryKey: true
  });

  const detailsPanel = useMemo(() => {
    if (shipmentQuery.isFetching || customerQuery.isFetching) {
      return <Skeleton />;
    }

    let data: any = {
      ...shipment,
      customer: customer?.pk,
      customer_name: customer?.name,
      customer_reference: shipment.order_detail?.customer_reference
    };

    // Top Left: Order / customer information
    let tl: DetailsField[] = [
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
        type: 'text',
        name: 'customer_reference',
        icon: 'serial',
        label: t`Customer Reference`,
        hidden: !data.customer_reference,
        copy: true
      }
    ];

    // Top right: Shipment information
    let tr: DetailsField[] = [
      {
        type: 'text',
        name: 'tracking_number',
        label: t`Tracking Number`,
        icon: 'trackable',
        copy: true
      },
      {
        type: 'text',
        name: 'invoice_number',
        label: t`Invoice Number`,
        icon: 'serial',
        copy: true
      }
    ];

    return (
      <>
        <ItemDetailsGrid>
          <Grid>
            <Grid.Col span={4}>
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
            </Grid.Col>
            <Grid.Col span={8}>
              <DetailsTable fields={tl} item={data} />
            </Grid.Col>
          </Grid>
          <DetailsTable fields={tr} item={data} />
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
        label: t`Assigned Items`,
        icon: <IconPackages />,
        content: <Skeleton />
      },
      AttachmentPanel({
        model_type: ModelType.salesordershipment,
        model_id: shipment.pk
      }),
      NotesPanel({
        model_type: ModelType.salesordershipment,
        model_id: shipment.pk
      })
    ];
  }, [shipment, detailsPanel]);

  const editShipment = useEditApiFormModal({
    url: ApiEndpoints.sales_order_shipment_list,
    pk: shipment.pk,
    fields: {},
    title: t`Edit Shipment`,
    onFormSuccess: refreshShipment
  });

  const shipmentActions = useMemo(() => {
    const canEdit: boolean = user.hasChangePermission(
      ModelType.salesordershipment
    );

    const isOpen = true; // TODO: Fix this

    return [
      <PrimaryActionButton
        title={t`Send Shipment`}
        icon="sales_orders"
        hidden={!isOpen}
        color="green"
        onClick={() => {
          // TODO: Ship the order
        }}
      />,
      <BarcodeActionDropdown
        model={ModelType.salesordershipment}
        pk={shipment.pk}
      />,
      <PrintingActions
        modelType={ModelType.salesordershipment}
        items={[shipment.pk]}
        enableLabels
        enableReports
      />,
      <OptionsActionDropdown
        tooltip={t`Shipment Actions`}
        actions={[
          EditItemAction({
            hidden: !canEdit,
            onClick: editShipment.open,
            tooltip: t`Edit Shipment`
          }),
          CancelItemAction({
            hidden: !isOpen,
            onClick: () => {
              // TODO: Delete the shipment
            },
            tooltip: t`Cancel Shipment`
          })
        ]}
      />
    ];
  }, [user, shipment]);

  return (
    <>
      {editShipment.modal}
      <InstanceDetail
        status={shipmentStatus}
        loading={shipmentQuery.isFetching || customerQuery.isFetching}
      >
        <Stack gap="xs">
          <PageDetail
            title={t`Sales Order Shipment` + `: ${shipment.reference}`}
            breadcrumbs={[
              { name: t`Sales`, url: '/sales/' },
              {
                name: shipment.order_detail?.reference,
                url: getDetailUrl(ModelType.salesorder, shipment.order)
              }
            ]}
            imageUrl={customer?.image}
            editAction={editShipment.open}
            editEnabled={user.hasChangePermission(ModelType.salesordershipment)}
            actions={shipmentActions}
          />
          <PanelGroup
            pageKey="salesordershipment"
            panels={shipmentPanels}
            model={ModelType.salesordershipment}
            instance={shipment}
            id={shipment.pk}
          />
        </Stack>
      </InstanceDetail>
    </>
  );
}
