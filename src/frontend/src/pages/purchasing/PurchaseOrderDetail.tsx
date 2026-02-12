import { t } from '@lingui/core/macro';
import { Accordion, Grid, Skeleton, Stack } from '@mantine/core';
import { IconInfoCircle, IconList, IconPackages } from '@tabler/icons-react';
import { type ReactNode, useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
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
import ParametersPanel from '../../components/panels/ParametersPanel';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import { formatCurrency } from '../../defaults/formatters';
import { usePurchaseOrderFields } from '../../forms/PurchaseOrderForms';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import ExtraLineItemTable from '../../tables/general/ExtraLineItemTable';
import { PurchaseOrderLineItemTable } from '../../tables/purchasing/PurchaseOrderLineItemTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';

/**
 * Detail page for a single PurchaseOrder
 */
export default function PurchaseOrderDetail() {
  const { id } = useParams();

  const user = useUserState();
  const globalSettings = useGlobalSettingsState();

  const {
    instance: order,
    instanceQuery,
    refreshInstance
  } = useInstance({
    endpoint: ApiEndpoints.purchase_order_list,
    pk: id,
    params: {
      supplier_detail: true
    },
    refetchOnMount: true
  });

  const orderCurrency = useMemo(() => {
    return (
      order.order_currency ||
      order.supplier_detail?.currency ||
      globalSettings.getSetting('INVENTREE_DEFAULT_CURRENCY')
    );
  }, [order, globalSettings]);

  const purchaseOrderFields = usePurchaseOrderFields({});

  const duplicatePurchaseOrderFields = usePurchaseOrderFields({
    duplicateOrderId: order.pk
  });

  const editPurchaseOrder = useEditApiFormModal({
    url: ApiEndpoints.purchase_order_list,
    pk: id,
    title: t`Edit Purchase Order`,
    fields: purchaseOrderFields,
    onFormSuccess: () => {
      refreshInstance();
    }
  });

  const poStatus = useStatusCodes({ modelType: ModelType.purchaseorder });

  const orderOpen: boolean = useMemo(() => {
    return (
      order.status == poStatus.PENDING ||
      order.status == poStatus.PLACED ||
      order.status == poStatus.ON_HOLD
    );
  }, [order, poStatus]);

  const lineItemsEditable: boolean = useMemo(() => {
    if (orderOpen) {
      return true;
    } else {
      return globalSettings.isSet('PURCHASEORDER_EDIT_COMPLETED_ORDERS');
    }
  }, [orderOpen, globalSettings]);

  const duplicatePurchaseOrderInitialData = useMemo(() => {
    const data = { ...order };
    // if we set the reference to null/undefined, it will be left blank in the form
    // if we omit the reference altogether, it will be auto-generated via reference pattern
    // from the OPTIONS response
    delete data.reference;
    return data;
  }, [order]);

  const duplicatePurchaseOrder = useCreateApiFormModal({
    url: ApiEndpoints.purchase_order_list,
    title: t`Add Purchase Order`,
    fields: duplicatePurchaseOrderFields,
    initialData: duplicatePurchaseOrderInitialData,
    follow: true,
    modelType: ModelType.purchaseorder
  });

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
        name: 'supplier_reference',
        label: t`Supplier Reference`,
        icon: 'reference',
        hidden: !order.supplier_reference,
        copy: true
      },
      {
        type: 'link',
        name: 'supplier',
        icon: 'suppliers',
        label: t`Supplier`,
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
        model: ModelType.purchaseorder
      },
      {
        type: 'status',
        name: 'status_custom_key',
        label: t`Custom Status`,
        model: ModelType.purchaseorder,
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
        progress: order.completed_lines
      },
      {
        type: 'link',
        model: ModelType.stocklocation,
        link: true,
        name: 'destination',
        label: t`Destination`,
        hidden: !order.destination
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
            currency: order?.order_currency || order?.supplier_detail?.currency
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
        type: 'text',
        name: 'contact_detail.name',
        label: t`Contact`,
        icon: 'user',
        copy: true,
        hidden: !order.contact
      },
      {
        type: 'text',
        name: 'contact_detail.email',
        label: t`Contact Email`,
        icon: 'email',
        copy: true,
        hidden: !order.contact_detail?.email
      },
      {
        type: 'text',
        name: 'contact_detail.phone',
        label: t`Contact Phone`,
        icon: 'phone',
        copy: true,
        hidden: !order.contact_detail?.phone
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
        icon: 'calendar'
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
        copy: true,
        hidden: !order.start_date
      },
      {
        type: 'date',
        name: 'target_date',
        label: t`Target Date`,
        icon: 'calendar',
        copy: true,
        hidden: !order.target_date
      },
      {
        type: 'date',
        name: 'complete_date',
        icon: 'calendar_check',
        label: t`Completion Date`,
        copy: true,
        hidden: !order.complete_date
      }
    ];

    return (
      <ItemDetailsGrid>
        <Grid grow>
          <DetailsImage
            appRole={UserRoles.purchase_order}
            apiPath={ApiEndpoints.company_list}
            src={order.supplier_detail?.image}
            pk={order.supplier}
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
                <PurchaseOrderLineItemTable
                  order={order}
                  orderDetailRefresh={refreshInstance}
                  currency={orderCurrency}
                  orderId={Number(id)}
                  editable={lineItemsEditable}
                  supplierId={Number(order.supplier)}
                />
              </Accordion.Panel>
            </Accordion.Item>
            <Accordion.Item value='extra-items' key='extraitems'>
              <Accordion.Control>
                <StylishText size='lg'>{t`Extra Line Items`}</StylishText>
              </Accordion.Control>
              <Accordion.Panel>
                <ExtraLineItemTable
                  endpoint={ApiEndpoints.purchase_order_extra_line_list}
                  orderId={order.pk}
                  orderDetailRefresh={refreshInstance}
                  currency={orderCurrency}
                  editable={lineItemsEditable}
                  role={UserRoles.purchase_order}
                />
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>
        )
      },
      {
        name: 'received-stock',
        label: t`Received Stock`,
        icon: <IconPackages />,
        content: (
          <StockItemTable
            tableName='received-stock'
            params={{
              purchase_order: id
            }}
          />
        )
      },
      ParametersPanel({
        model_type: ModelType.purchaseorder,
        model_id: order.pk
      }),
      AttachmentPanel({
        model_type: ModelType.purchaseorder,
        model_id: order.pk
      }),
      NotesPanel({
        model_type: ModelType.purchaseorder,
        model_id: order.pk,
        has_note: !!order.notes
      })
    ];
  }, [order, id, user]);

  const issueOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.purchase_order_issue, order.pk),
    title: t`Issue Purchase Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Issue this order`,
    successMessage: t`Order issued`
  });

  const cancelOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.purchase_order_cancel, order.pk),
    title: t`Cancel Purchase Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Cancel this order`,
    successMessage: t`Order cancelled`
  });

  const holdOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.purchase_order_hold, order.pk),
    title: t`Hold Purchase Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Place this order on hold`,
    successMessage: t`Order placed on hold`
  });

  const completeOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.purchase_order_complete, order.pk),
    title: t`Complete Purchase Order`,
    successMessage: t`Order completed`,
    timeout: 10000,
    fields: {
      accept_incomplete: {}
    },
    onFormSuccess: refreshInstance,
    preFormWarning: t`Mark this order as complete`
  });

  const poActions = useMemo(() => {
    const canEdit: boolean = user.hasChangeRole(UserRoles.purchase_order);

    const canIssue: boolean =
      canEdit &&
      (order.status == poStatus.PENDING || order.status == poStatus.ON_HOLD);

    const canHold: boolean =
      canEdit &&
      (order.status == poStatus.PENDING || order.status == poStatus.PLACED);

    const canComplete: boolean = canEdit && order.status == poStatus.PLACED;

    const canCancel: boolean =
      canEdit &&
      order.status != poStatus.CANCELLED &&
      order.status != poStatus.COMPLETE;

    return [
      <PrimaryActionButton
        title={t`Issue Order`}
        icon='issue'
        hidden={!canIssue}
        color='blue'
        onClick={issueOrder.open}
      />,
      <PrimaryActionButton
        title={t`Complete Order`}
        icon='complete'
        hidden={!canComplete}
        color='green'
        onClick={completeOrder.open}
      />,
      <AdminButton model={ModelType.purchaseorder} id={order.pk} />,
      <BarcodeActionDropdown
        model={ModelType.purchaseorder}
        pk={order.pk}
        hash={order?.barcode_hash}
      />,
      <PrintingActions
        modelType={ModelType.purchaseorder}
        items={[order.pk]}
        enableLabels
        enableReports
      />,
      <OptionsActionDropdown
        tooltip={t`Order Actions`}
        actions={[
          EditItemAction({
            hidden: !canEdit,
            tooltip: t`Edit order`,
            onClick: () => {
              editPurchaseOrder.open();
            }
          }),
          DuplicateItemAction({
            hidden: !user.hasAddRole(UserRoles.purchase_order),
            onClick: () => duplicatePurchaseOrder.open(),
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
  }, [id, order, user, poStatus]);

  const orderBadges: ReactNode[] = useMemo(() => {
    return instanceQuery.isLoading
      ? []
      : [
          <StatusRenderer
            status={order.status_custom_key}
            type={ModelType.purchaseorder}
            options={{ size: 'lg' }}
          />
        ];
  }, [order, instanceQuery]);

  const subtitle: string = useMemo(() => {
    let t = order.supplier_detail?.name || '';

    if (order.supplier_reference) {
      t += ` (${order.supplier_reference})`;
    }

    return t;
  }, [order]);

  return (
    <>
      {issueOrder.modal}
      {holdOrder.modal}
      {cancelOrder.modal}
      {completeOrder.modal}
      {editPurchaseOrder.modal}
      {duplicatePurchaseOrder.modal}
      <InstanceDetail
        query={instanceQuery}
        requiredRole={UserRoles.purchase_order}
      >
        <Stack gap='xs'>
          <PageDetail
            title={`${t`Purchase Order`}: ${order.reference}`}
            subtitle={subtitle}
            imageUrl={order.supplier_detail?.image}
            breadcrumbs={[{ name: t`Purchasing`, url: '/purchasing/' }]}
            lastCrumb={[
              {
                name: order.reference,
                url: `/purchasing/purchase-order/${order.pk}`
              }
            ]}
            actions={poActions}
            badges={orderBadges}
            editAction={editPurchaseOrder.open}
            editEnabled={user.hasChangePermission(ModelType.purchaseorder)}
          />
          <PanelGroup
            pageKey='purchaseorder'
            panels={orderPanels}
            model={ModelType.purchaseorder}
            instance={order}
            reloadInstance={refreshInstance}
            id={order.pk}
          />
        </Stack>
      </InstanceDetail>
    </>
  );
}
