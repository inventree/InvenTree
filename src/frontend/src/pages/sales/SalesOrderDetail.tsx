import { StylishText } from '@lib/components/StylishText';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { PanelType } from '@lib/types/Panel';
import { t } from '@lingui/core/macro';
import { Accordion, Skeleton, Stack } from '@mantine/core';
import {
  IconBookmark,
  IconCubeSend,
  IconInfoCircle,
  IconList,
  IconTools
} from '@tabler/icons-react';
import { type ReactNode, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import AdminButton from '../../components/buttons/AdminButton';
import PrimaryActionButton from '../../components/buttons/PrimaryActionButton';
import { PrintingActions } from '../../components/buttons/PrintingActions';
import {
  BarcodeActionDropdown,
  CancelItemAction,
  DuplicateItemAction,
  EditItemAction,
  HoldItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import AttachmentPanel from '../../components/panels/AttachmentPanel';
import NotesPanel from '../../components/panels/NotesPanel';
import { PanelGroup } from '../../components/panels/PanelGroup';
import ParametersPanel from '../../components/panels/ParametersPanel';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import { useSalesOrderFields } from '../../forms/SalesOrderForms';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import { BuildOrderTable } from '../../tables/build/BuildOrderTable';
import ExtraLineItemTable from '../../tables/general/ExtraLineItemTable';
import SalesOrderAllocationTable from '../../tables/sales/SalesOrderAllocationTable';
import SalesOrderLineItemTable from '../../tables/sales/SalesOrderLineItemTable';
import SalesOrderShipmentTable from '../../tables/sales/SalesOrderShipmentTable';
import { SalesOrderDetailsPanel } from './SalesOrderDetailsPanel';

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
    refreshInstance
  } = useInstance({
    endpoint: ApiEndpoints.sales_order_list,
    pk: id,
    params: {
      customer_detail: true,
      tags: true
    }
  });

  const orderCurrency = useMemo(() => {
    return (
      order.order_currency ||
      order.customer_detail?.currency ||
      globalSettings.getSetting('INVENTREE_DEFAULT_CURRENCY')
    );
  }, [order, globalSettings]);

  const soStatus = useStatusCodes({ modelType: ModelType.salesorder });

  const lineItemsEditable: boolean = useMemo(() => {
    const orderOpen: boolean =
      order.status != soStatus.COMPLETE && order.status != soStatus.CANCELLED;

    if (orderOpen) {
      return true;
    } else {
      return globalSettings.isSet('SALESORDER_EDIT_COMPLETED_ORDERS');
    }
  }, [globalSettings, order.status, soStatus]);

  const salesOrderFields = useSalesOrderFields({});

  const editSalesOrder = useEditApiFormModal({
    url: ApiEndpoints.sales_order_list,
    pk: order.pk,
    title: t`Edit Sales Order`,
    fields: salesOrderFields,
    queryParams: new URLSearchParams({ tags: 'true' }),
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
        content: (
          <SalesOrderDetailsPanel
            instance={order}
            allowImageEdit
            refreshInstance={refreshInstance}
          />
        )
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
                  orderDetailRefresh={refreshInstance}
                  currency={orderCurrency}
                  customerId={order.customer}
                  editable={lineItemsEditable}
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
                  editable={lineItemsEditable}
                  orderDetailRefresh={refreshInstance}
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
        icon: <IconCubeSend />,
        content: (
          <SalesOrderShipmentTable
            orderId={order.pk}
            customerId={order.customer}
          />
        )
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
      ParametersPanel({
        model_type: ModelType.salesorder,
        model_id: order.pk
      }),
      AttachmentPanel({
        model_type: ModelType.salesorder,
        model_id: order.pk
      }),
      NotesPanel({
        model_type: ModelType.salesorder,
        model_id: order.pk,
        has_note: !!order.notes,
        // TODO @matmair - change API to include a "locked" attribute that we can check here
        editable:
          order.status == soStatus.COMPLETE &&
          !globalSettings.isSet('SALESORDER_EDIT_COMPLETED_ORDERS')
            ? false
            : undefined
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

    const autoComplete = globalSettings.isSet('SALESORDER_SHIP_COMPLETE');

    const canShip: boolean =
      !autoComplete && canEdit && order.status == soStatus.IN_PROGRESS;
    const canComplete: boolean =
      canEdit &&
      (order.status == soStatus.SHIPPED ||
        (autoComplete && order.status == soStatus.IN_PROGRESS));

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
        enableLabels
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
  }, [user, order, soStatus, globalSettings]);

  const orderBadges: ReactNode[] = useMemo(() => {
    return instanceQuery.isLoading
      ? []
      : [
          <StatusRenderer
            status={order.status_custom_key || order.status}
            type={ModelType.salesorder}
            options={{ size: 'lg' }}
            key={order.pk}
          />
        ];
  }, [order, instanceQuery]);

  const subtitle: string = useMemo(() => {
    let t = order.customer_detail?.name || '';

    if (order.customer_reference) {
      t += ` (${order.customer_reference})`;
    }

    return t;
  }, [order]);

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
        query={instanceQuery}
        requiredRole={UserRoles.sales_order}
      >
        <Stack gap='xs'>
          <PageDetail
            title={`${t`Sales Order`}: ${order.reference}`}
            subtitle={subtitle}
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
            reloadInstance={refreshInstance}
            instance={order}
            id={order.pk}
          />
        </Stack>
      </InstanceDetail>
    </>
  );
}
