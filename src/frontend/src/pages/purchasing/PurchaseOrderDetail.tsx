import { t } from '@lingui/macro';
import { Grid, Skeleton, Stack } from '@mantine/core';
import {
  IconDots,
  IconInfoCircle,
  IconList,
  IconNotes,
  IconPackages,
  IconPaperclip
} from '@tabler/icons-react';
import { ReactNode, useMemo } from 'react';
import { useParams } from 'react-router-dom';

import AdminButton from '../../components/buttons/AdminButton';
import { PrintingActions } from '../../components/buttons/PrintingActions';
import { DetailsField, DetailsTable } from '../../components/details/Details';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import NotesEditor from '../../components/editors/NotesEditor';
import {
  ActionDropdown,
  BarcodeActionDropdown,
  CancelItemAction,
  DuplicateItemAction,
  EditItemAction,
  LinkBarcodeAction,
  UnlinkBarcodeAction,
  ViewBarcodeAction
} from '../../components/items/ActionDropdown';
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
import { useUserState } from '../../states/UserState';
import { AttachmentTable } from '../../tables/general/AttachmentTable';
import { PurchaseOrderLineItemTable } from '../../tables/purchasing/PurchaseOrderLineItemTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';

/**
 * Detail page for a single PurchaseOrder
 */
export default function PurchaseOrderDetail() {
  const { id } = useParams();

  const user = useUserState();

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
        type: 'text',
        name: 'line_items',
        label: t`Line Items`,
        icon: 'list'
      },
      {
        type: 'progressbar',
        name: 'completed',
        icon: 'progress',
        label: t`Completed Line Items`,
        total: order.line_items,
        progress: order.completed_lines
      },
      {
        type: 'progressbar',
        name: 'shipments',
        icon: 'shipment',
        label: t`Completed Shipments`,
        total: order.shipments,
        progress: order.completed_shipments
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
          <PurchaseOrderLineItemTable
            orderId={Number(id)}
            supplierId={Number(order.supplier)}
          />
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

  const poActions = useMemo(() => {
    return [
      <AdminButton model={ModelType.purchaseorder} pk={order.pk} />,
      <BarcodeActionDropdown
        actions={[
          ViewBarcodeAction({}),
          LinkBarcodeAction({
            hidden: order?.barcode_hash
          }),
          UnlinkBarcodeAction({
            hidden: !order?.barcode_hash
          })
        ]}
      />,
      <PrintingActions
        modelType={ModelType.purchaseorder}
        items={[order.pk]}
        enableReports
      />,
      <ActionDropdown
        tooltip={t`Order Actions`}
        icon={<IconDots />}
        actions={[
          EditItemAction({
            hidden: !user.hasChangeRole(UserRoles.purchase_order),
            onClick: () => {
              editPurchaseOrder.open();
            }
          }),
          CancelItemAction({
            tooltip: t`Cancel order`
          }),
          DuplicateItemAction({
            hidden: !user.hasAddRole(UserRoles.purchase_order),
            onClick: () => duplicatePurchaseOrder.open()
          })
        ]}
      />
    ];
  }, [id, order, user]);

  const orderBadges: ReactNode[] = useMemo(() => {
    return instanceQuery.isLoading
      ? []
      : [
          <StatusRenderer
            status={order.status}
            type={ModelType.purchaseorder}
            options={{ size: 'lg' }}
          />
        ];
  }, [order, instanceQuery]);

  return (
    <>
      {editPurchaseOrder.modal}
      <InstanceDetail status={requestStatus} loading={instanceQuery.isFetching}>
        <Stack gap="xs">
          <PageDetail
            title={t`Purchase Order` + `: ${order.reference}`}
            subtitle={order.description}
            imageUrl={order.supplier_detail?.image}
            breadcrumbs={[{ name: t`Purchasing`, url: '/purchasing/' }]}
            actions={poActions}
            badges={orderBadges}
          />
          <PanelGroup pageKey="purchaseorder" panels={orderPanels} />
        </Stack>
      </InstanceDetail>
    </>
  );
}
