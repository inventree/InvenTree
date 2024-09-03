import { t } from '@lingui/macro';
import { Accordion, Grid, Skeleton, Stack } from '@mantine/core';
import {
  IconInfoCircle,
  IconList,
  IconNotes,
  IconPackages,
  IconPaperclip
} from '@tabler/icons-react';
import { ReactNode, useMemo } from 'react';
import { useParams } from 'react-router-dom';

import AdminButton from '../../components/buttons/AdminButton';
import PrimaryActionButton from '../../components/buttons/PrimaryActionButton';
import { PrintingActions } from '../../components/buttons/PrintingActions';
import { DetailsField, DetailsTable } from '../../components/details/Details';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import NotesEditor from '../../components/editors/NotesEditor';
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
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import { formatCurrency } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { usePurchaseOrderFields } from '../../forms/PurchaseOrderForms';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { apiUrl } from '../../states/ApiState';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';
import { AttachmentTable } from '../../tables/general/AttachmentTable';
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
    refreshInstance,
    requestStatus
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

  const purchaseOrderFields = usePurchaseOrderFields();

  const editPurchaseOrder = useEditApiFormModal({
    url: ApiEndpoints.purchase_order_list,
    pk: id,
    title: t`Edit Purchase Order`,
    fields: purchaseOrderFields,
    onFormSuccess: () => {
      refreshInstance();
    }
  });

  const duplicatePurchaseOrder = useCreateApiFormModal({
    url: ApiEndpoints.purchase_order_list,
    title: t`Add Purchase Order`,
    fields: purchaseOrderFields,
    initialData: {
      ...order,
      reference: undefined
    },
    follow: true,
    modelType: ModelType.purchaseorder
  });

  const detailsPanel = useMemo(() => {
    if (instanceQuery.isFetching) {
      return <Skeleton />;
    }

    let tl: DetailsField[] = [
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
      }
    ];

    let tr: DetailsField[] = [
      {
        type: 'progressbar',
        name: 'completed',
        icon: 'progress',
        label: t`Completed Line Items`,
        total: order.line_items,
        progress: order.completed_lines
      },
      {
        type: 'text',
        name: 'currency',
        label: t`Order Currency`,
        value_formatter: () =>
          order?.order_currency ?? order?.supplier_detail?.currency
      },
      {
        type: 'text',
        name: 'total_price',
        label: t`Total Cost`,
        value_formatter: () => {
          return formatCurrency(order?.total_price, {
            currency: order?.order_currency ?? order?.supplier_detail?.currency
          });
        }
      }
    ];

    let bl: DetailsField[] = [
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
      }
      // TODO: Project code
    ];

    let br: DetailsField[] = [
      {
        type: 'text',
        name: 'creation_date',
        label: t`Created On`,
        icon: 'calendar'
      },
      {
        type: 'text',
        name: 'target_date',
        label: t`Target Date`,
        icon: 'calendar',
        hidden: !order.target_date
      },
      {
        type: 'text',
        name: 'responsible',
        label: t`Responsible`,
        badge: 'owner',
        hidden: !order.responsible
      }
    ];

    return (
      <ItemDetailsGrid>
        <Grid>
          <Grid.Col span={4}>
            <DetailsImage
              appRole={UserRoles.purchase_order}
              apiPath={ApiEndpoints.company_list}
              src={order.supplier_detail?.image}
              pk={order.supplier}
            />
          </Grid.Col>
          <Grid.Col span={8}>
            <DetailsTable fields={tl} item={order} />
          </Grid.Col>
        </Grid>
        <DetailsTable fields={tr} item={order} />
        <DetailsTable fields={bl} item={order} />
        <DetailsTable fields={br} item={order} />
      </ItemDetailsGrid>
    );
  }, [order, instanceQuery]);

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
            <Accordion.Item value="line-items" key="lineitems">
              <Accordion.Control>
                <StylishText size="lg">{t`Line Items`}</StylishText>
              </Accordion.Control>
              <Accordion.Panel>
                <PurchaseOrderLineItemTable
                  order={order}
                  currency={orderCurrency}
                  orderId={Number(id)}
                  supplierId={Number(order.supplier)}
                />
              </Accordion.Panel>
            </Accordion.Item>
            <Accordion.Item value="extra-items" key="extraitems">
              <Accordion.Control>
                <StylishText size="lg">{t`Extra Line Items`}</StylishText>
              </Accordion.Control>
              <Accordion.Panel>
                <ExtraLineItemTable
                  endpoint={ApiEndpoints.purchase_order_extra_line_list}
                  orderId={order.pk}
                  currency={orderCurrency}
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
            tableName="received-stock"
            params={{
              purchase_order: id
            }}
          />
        )
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip />,
        content: (
          <AttachmentTable
            model_type={ModelType.purchaseorder}
            model_id={order.pk}
          />
        )
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes />,
        content: (
          <NotesEditor
            modelType={ModelType.purchaseorder}
            modelId={order.pk}
            editable={user.hasChangeRole(UserRoles.purchase_order)}
          />
        )
      }
    ];
  }, [order, id, user]);

  const poStatus = useStatusCodes({ modelType: ModelType.purchaseorder });

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
        icon="issue"
        hidden={!canIssue}
        color="blue"
        onClick={issueOrder.open}
      />,
      <PrimaryActionButton
        title={t`Complete Order`}
        icon="complete"
        hidden={!canComplete}
        color="green"
        onClick={completeOrder.open}
      />,
      <AdminButton model={ModelType.purchaseorder} pk={order.pk} />,
      <BarcodeActionDropdown
        model={ModelType.purchaseorder}
        pk={order.pk}
        hash={order?.barcode_hash}
      />,
      <PrintingActions
        modelType={ModelType.purchaseorder}
        items={[order.pk]}
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

  return (
    <>
      {issueOrder.modal}
      {holdOrder.modal}
      {cancelOrder.modal}
      {completeOrder.modal}
      {editPurchaseOrder.modal}
      {duplicatePurchaseOrder.modal}
      <InstanceDetail status={requestStatus} loading={instanceQuery.isFetching}>
        <Stack gap="xs">
          <PageDetail
            title={t`Purchase Order` + `: ${order.reference}`}
            subtitle={order.description}
            imageUrl={order.supplier_detail?.image}
            breadcrumbs={[{ name: t`Purchasing`, url: '/purchasing/' }]}
            actions={poActions}
            badges={orderBadges}
            editAction={editPurchaseOrder.open}
            editEnabled={user.hasChangePermission(ModelType.purchaseorder)}
          />
          <PanelGroup pageKey="purchaseorder" panels={orderPanels} />
        </Stack>
      </InstanceDetail>
    </>
  );
}
