import { t } from '@lingui/macro';
import { Accordion, Grid, Skeleton, Stack } from '@mantine/core';
import {
  IconBookmark,
  IconInfoCircle,
  IconList,
  IconTools,
  IconTruckDelivery
} from '@tabler/icons-react';
import { type ReactNode, useMemo } from 'react';
import { useParams } from 'react-router-dom';

import AdminButton from '../../components/buttons/AdminButton';
import PrimaryActionButton from '../../components/buttons/PrimaryActionButton';
import { PrintingActions } from '../../components/buttons/PrintingActions';
import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import {
  BarcodeActionDropdown,
  CancelItemAction,
  DuplicateItemAction,
  EditItemAction,
  HoldItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import { StylishText } from '../../components/items/StylishText';
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import AttachmentPanel from '../../components/panels/AttachmentPanel';
import NotesPanel from '../../components/panels/NotesPanel';
import type { PanelType } from '../../components/panels/Panel';
import { PanelGroup } from '../../components/panels/PanelGroup';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import { formatCurrency } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useSalesOrderFields } from '../../forms/SalesOrderForms';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { apiUrl } from '../../states/ApiState';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';
import { BuildOrderTable } from '../../tables/build/BuildOrderTable';
import ExtraLineItemTable from '../../tables/general/ExtraLineItemTable';
import SalesOrderAllocationTable from '../../tables/sales/SalesOrderAllocationTable';
import SalesOrderLineItemTable from '../../tables/sales/SalesOrderLineItemTable';
import SalesOrderShipmentTable from '../../tables/sales/SalesOrderShipmentTable';

/**
 * Detail page for a single SalesOrder
 */
export default function SalesOrderDetail() {
  const { id } = useParams();

  const user = useUserState();

  const globalSettings = useGlobalSettingsState();

  const {
    instance: order,
    instanceQuery,
    refreshInstance,
    requestStatus
  } = useInstance({
    endpoint: ApiEndpoints.sales_order_list,
    pk: id,
    params: {
      customer_detail: true
    }
  });

  const orderCurrency = useMemo(() => {
    return (
      order.order_currency ||
      order.customer_detail?.currency ||
      globalSettings.getSetting('INVENTREE_DEFAULT_CURRENCY')
    );
  }, [order, globalSettings]);

  const detailsPanel = useMemo(() => {
    if (instanceQuery.isFetching) {
      return <Skeleton />;
    }

    const tl: DetailsField[] = [
      {
        type: 'text',
        name: 'reference',
        label: t`Reference`,
        copy: true
      },
      {
        type: 'text',
        name: 'customer_reference',
        label: t`Customer Reference`,
        copy: true,
        icon: 'reference',
        hidden: !order.customer_reference
      },
      {
        type: 'link',
        name: 'customer',
        icon: 'customers',
        label: t`Customer`,
        model: ModelType.company
      },
      {
        type: 'text',
        name: 'description',
        label: t`Description`,
        copy: true
      },
      {
        type: 'status',
        name: 'status',
        label: t`Status`,
        model: ModelType.salesorder
      },
      {
        type: 'status',
        name: 'status_custom_key',
        label: t`Custom Status`,
        model: ModelType.salesorder,
        icon: 'status',
        hidden:
          !order.status_custom_key || order.status_custom_key == order.status
      }
    ];

    const tr: DetailsField[] = [
      {
        type: 'progressbar',
        name: 'completed',
        icon: 'progress',
        label: t`Completed Line Items`,
        total: order.line_items,
        progress: order.completed_lines,
        hidden: !order.line_items
      },
      {
        type: 'progressbar',
        name: 'shipments',
        icon: 'shipment',
        label: t`Completed Shipments`,
        total: order.shipments_count,
        progress: order.completed_shipments_count,
        hidden: !order.shipments_count
      },
      {
        type: 'text',
        name: 'currency',
        label: t`Order Currency`,
        value_formatter: () => orderCurrency
      },
      {
        type: 'text',
        name: 'total_price',
        label: t`Total Cost`,
        value_formatter: () => {
          return formatCurrency(order?.total_price, {
            currency: orderCurrency
          });
        }
      }
    ];

    const bl: DetailsField[] = [
      {
        type: 'link',
        external: true,
        name: 'link',
        label: t`Link`,
        copy: true,
        hidden: !order.link
      },
      {
        type: 'link',
        model: ModelType.contact,
        link: false,
        name: 'contact',
        label: t`Contact`,
        icon: 'user',
        copy: true,
        hidden: !order.contact
      },
      {
        type: 'text',
        name: 'project_code_label',
        label: t`Project Code`,
        icon: 'reference',
        copy: true,
        hidden: !order.project_code
      },
      {
        type: 'text',
        name: 'responsible',
        label: t`Responsible`,
        badge: 'owner',
        hidden: !order.responsible
      }
    ];

    const br: DetailsField[] = [
      {
        type: 'date',
        name: 'creation_date',
        label: t`Creation Date`,
        copy: true,
        hidden: !order.creation_date
      },
      {
        type: 'date',
        name: 'issue_date',
        label: t`Issue Date`,
        icon: 'calendar',
        copy: true,
        hidden: !order.issue_date
      },
      {
        type: 'date',
        name: 'start_date',
        label: t`Start Date`,
        icon: 'calendar',
        hidden: !order.start_date,
        copy: true
      },
      {
        type: 'date',
        name: 'target_date',
        label: t`Target Date`,
        hidden: !order.target_date,
        copy: true
      },
      {
        type: 'date',
        name: 'shipment_date',
        label: t`Completion Date`,
        hidden: !order.shipment_date,
        copy: true
      }
    ];

    return (
      <ItemDetailsGrid>
        <Grid grow>
          <DetailsImage
            appRole={UserRoles.purchase_order}
            apiPath={ApiEndpoints.company_list}
            src={order.customer_detail?.image}
            pk={order.customer}
          />
          <Grid.Col span={{ base: 12, sm: 8 }}>
            <DetailsTable fields={tl} item={order} />
          </Grid.Col>
        </Grid>
        <DetailsTable fields={tr} item={order} />
        <DetailsTable fields={bl} item={order} />
        <DetailsTable fields={br} item={order} />
      </ItemDetailsGrid>
    );
  }, [order, orderCurrency, instanceQuery]);

  const soStatus = useStatusCodes({ modelType: ModelType.salesorder });

  const salesOrderFields = useSalesOrderFields({});

  const editSalesOrder = useEditApiFormModal({
    url: ApiEndpoints.sales_order_list,
    pk: order.pk,
    title: t`Edit Sales Order`,
    fields: salesOrderFields,
    onFormSuccess: () => {
      refreshInstance();
    }
  });

  const duplicateOrderFields = useSalesOrderFields({
    duplicateOrderId: order.pk
  });

  const duplicateSalesOrderInitialData = useMemo(() => {
    const data = { ...order };
    // if we set the reference to null/undefined, it will be left blank in the form
    // if we omit the reference altogether, it will be auto-generated via reference pattern
    // from the OPTIONS response
    delete data.reference;
    return data;
  }, [order]);

  const duplicateSalesOrder = useCreateApiFormModal({
    url: ApiEndpoints.sales_order_list,
    title: t`Add Sales Order`,
    fields: duplicateOrderFields,
    initialData: duplicateSalesOrderInitialData,
    follow: true,
    modelType: ModelType.salesorder
  });

  const orderPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'detail',
        label: t`Order Details`,
        icon: <IconInfoCircle />,
        content: detailsPanel
      },
      {
        name: 'line-items',
        label: t`Line Items`,
        icon: <IconList />,
        content: (
          <Accordion
            multiple={true}
            defaultValue={['line-items', 'extra-items']}
          >
            <Accordion.Item value='line-items' key='lineitems'>
              <Accordion.Control>
                <StylishText size='lg'>{t`Line Items`}</StylishText>
              </Accordion.Control>
              <Accordion.Panel>
                <SalesOrderLineItemTable
                  orderId={order.pk}
                  currency={orderCurrency}
                  customerId={order.customer}
                  editable={
                    order.status != soStatus.COMPLETE &&
                    order.status != soStatus.CANCELLED
                  }
                />
              </Accordion.Panel>
            </Accordion.Item>
            <Accordion.Item value='extra-items' key='extraitems'>
              <Accordion.Control>
                <StylishText size='lg'>{t`Extra Line Items`}</StylishText>
              </Accordion.Control>
              <Accordion.Panel>
                <ExtraLineItemTable
                  endpoint={ApiEndpoints.sales_order_extra_line_list}
                  orderId={order.pk}
                  currency={orderCurrency}
                  role={UserRoles.sales_order}
                />
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>
        )
      },
      {
        name: 'shipments',
        label: t`Shipments`,
        icon: <IconTruckDelivery />,
        content: <SalesOrderShipmentTable orderId={order.pk} />
      },
      {
        name: 'allocations',
        label: t`Allocated Stock`,
        icon: <IconBookmark />,
        content: (
          <SalesOrderAllocationTable
            orderId={order.pk}
            showPartInfo
            allowEdit
            modelField='item'
            modelTarget={ModelType.stockitem}
          />
        )
      },
      {
        name: 'build-orders',
        label: t`Build Orders`,
        icon: <IconTools />,
        hidden: !user.hasViewRole(UserRoles.build),
        content: order?.pk ? (
          <BuildOrderTable salesOrderId={order.pk} />
        ) : (
          <Skeleton />
        )
      },
      AttachmentPanel({
        model_type: ModelType.salesorder,
        model_id: order.pk
      }),
      NotesPanel({
        model_type: ModelType.salesorder,
        model_id: order.pk
      })
    ];
  }, [order, id, user, soStatus, user]);

  const issueOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.sales_order_issue, order.pk),
    title: t`Issue Sales Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Issue this order`,
    successMessage: t`Order issued`
  });

  const cancelOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.sales_order_cancel, order.pk),
    title: t`Cancel Sales Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Cancel this order`,
    successMessage: t`Order cancelled`
  });

  const holdOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.sales_order_hold, order.pk),
    title: t`Hold Sales Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Place this order on hold`,
    successMessage: t`Order placed on hold`
  });

  const shipOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.sales_order_complete, order.pk),
    title: t`Ship Sales Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Ship this order?`,
    successMessage: t`Order shipped`,
    fields: {
      accept_incomplete: {}
    }
  });

  const completeOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.sales_order_complete, order.pk),
    title: t`Complete Sales Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Mark this order as complete`,
    successMessage: t`Order completed`,
    fields: {
      accept_incomplete: {}
    }
  });

  const soActions = useMemo(() => {
    const canEdit: boolean = user.hasChangeRole(UserRoles.sales_order);

    const canIssue: boolean =
      canEdit &&
      (order.status == soStatus.PENDING || order.status == soStatus.ON_HOLD);

    const canCancel: boolean =
      canEdit &&
      (order.status == soStatus.PENDING ||
        order.status == soStatus.ON_HOLD ||
        order.status == soStatus.IN_PROGRESS);

    const canHold: boolean =
      canEdit &&
      (order.status == soStatus.PENDING ||
        order.status == soStatus.IN_PROGRESS);

    const canShip: boolean = canEdit && order.status == soStatus.IN_PROGRESS;
    const canComplete: boolean = canEdit && order.status == soStatus.SHIPPED;

    return [
      <PrimaryActionButton
        title={t`Issue Order`}
        icon='issue'
        hidden={!canIssue}
        color='blue'
        onClick={issueOrder.open}
      />,
      <PrimaryActionButton
        title={t`Ship Order`}
        icon='deliver'
        hidden={!canShip}
        color='blue'
        onClick={shipOrder.open}
      />,
      <PrimaryActionButton
        title={t`Complete Order`}
        icon='complete'
        hidden={!canComplete}
        color='green'
        onClick={completeOrder.open}
      />,
      <AdminButton model={ModelType.salesorder} id={order.pk} />,
      <BarcodeActionDropdown
        model={ModelType.salesorder}
        pk={order.pk}
        hash={order?.barcode_hash}
      />,
      <PrintingActions
        modelType={ModelType.salesorder}
        items={[order.pk]}
        enableReports
      />,
      <OptionsActionDropdown
        tooltip={t`Order Actions`}
        actions={[
          EditItemAction({
            hidden: !canEdit,
            onClick: editSalesOrder.open,
            tooltip: t`Edit order`
          }),
          DuplicateItemAction({
            hidden: !user.hasAddRole(UserRoles.sales_order),
            onClick: duplicateSalesOrder.open,
            tooltip: t`Duplicate order`
          }),
          HoldItemAction({
            tooltip: t`Hold order`,
            hidden: !canHold,
            onClick: holdOrder.open
          }),
          CancelItemAction({
            tooltip: t`Cancel order`,
            hidden: !canCancel,
            onClick: cancelOrder.open
          })
        ]}
      />
    ];
  }, [user, order, soStatus]);

  const orderBadges: ReactNode[] = useMemo(() => {
    return instanceQuery.isLoading
      ? []
      : [
          <StatusRenderer
            status={order.status_custom_key}
            type={ModelType.salesorder}
            options={{ size: 'lg' }}
            key={order.pk}
          />
        ];
  }, [order, instanceQuery]);

  return (
    <>
      {issueOrder.modal}
      {cancelOrder.modal}
      {holdOrder.modal}
      {shipOrder.modal}
      {completeOrder.modal}
      {editSalesOrder.modal}
      {duplicateSalesOrder.modal}
      <InstanceDetail
        status={requestStatus}
        loading={instanceQuery.isFetching}
        requiredRole={UserRoles.sales_order}
      >
        <Stack gap='xs'>
          <PageDetail
            title={`${t`Sales Order`}: ${order.reference}`}
            subtitle={order.description}
            imageUrl={order.customer_detail?.image}
            badges={orderBadges}
            actions={soActions}
            breadcrumbs={[{ name: t`Sales`, url: '/sales/' }]}
            lastCrumb={[
              { name: order.reference, url: `/sales/sales-order/${order.pk}` }
            ]}
            editAction={editSalesOrder.open}
            editEnabled={user.hasChangePermission(ModelType.salesorder)}
          />
          <PanelGroup
            pageKey='salesorder'
            panels={orderPanels}
            model={ModelType.salesorder}
            id={order.pk}
            instance={order}
          />
        </Stack>
      </InstanceDetail>
    </>
  );
}
