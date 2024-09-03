import { t } from '@lingui/macro';
import { Accordion, Grid, Skeleton, Stack } from '@mantine/core';
import {
  IconInfoCircle,
  IconList,
  IconNotes,
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
import { useReturnOrderFields } from '../../forms/SalesOrderForms';
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
import ReturnOrderLineItemTable from '../../tables/sales/ReturnOrderLineItemTable';

/**
 * Detail page for a single ReturnOrder
 */
export default function ReturnOrderDetail() {
  const { id } = useParams();

  const user = useUserState();

  const globalSettings = useGlobalSettingsState();

  const {
    instance: order,
    instanceQuery,
    refreshInstance,
    requestStatus
  } = useInstance({
    endpoint: ApiEndpoints.return_order_list,
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

    let tl: DetailsField[] = [
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
        model: ModelType.returnorder
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
        type: 'text',
        name: 'currency',
        label: t`Order Currency`,
        value_formatter: () =>
          order?.order_currency ?? order?.customer_detail?.currency
      },
      {
        type: 'text',
        name: 'total_price',
        label: t`Total Cost`,
        value_formatter: () => {
          return formatCurrency(order?.total_price, {
            currency: order?.order_currency ?? order?.customer_detail?.currency
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
              src={order.customer_detail?.image}
              pk={order.customer}
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
                <ReturnOrderLineItemTable
                  orderId={order.pk}
                  customerId={order.customer}
                  currency={orderCurrency}
                />
              </Accordion.Panel>
            </Accordion.Item>
            <Accordion.Item value="extra-items" key="extraitems">
              <Accordion.Control>
                <StylishText size="lg">{t`Extra Line Items`}</StylishText>
              </Accordion.Control>
              <Accordion.Panel>
                <ExtraLineItemTable
                  endpoint={ApiEndpoints.return_order_extra_line_list}
                  orderId={order.pk}
                  currency={orderCurrency}
                  role={UserRoles.return_order}
                />
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>
        )
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip />,
        content: (
          <AttachmentTable
            model_type={ModelType.returnorder}
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
            modelType={ModelType.returnorder}
            modelId={order.pk}
            editable={user.hasChangeRole(UserRoles.return_order)}
          />
        )
      }
    ];
  }, [order, id, user]);

  const orderBadges: ReactNode[] = useMemo(() => {
    return instanceQuery.isLoading
      ? []
      : [
          <StatusRenderer
            status={order.status_custom_key}
            type={ModelType.returnorder}
            options={{ size: 'lg' }}
          />
        ];
  }, [order, instanceQuery]);

  const returnOrderFields = useReturnOrderFields();

  const editReturnOrder = useEditApiFormModal({
    url: ApiEndpoints.return_order_list,
    pk: order.pk,
    title: t`Edit Return Order`,
    fields: returnOrderFields,
    onFormSuccess: () => {
      refreshInstance();
    }
  });

  const duplicateReturnOrder = useCreateApiFormModal({
    url: ApiEndpoints.return_order_list,
    title: t`Add Return Order`,
    fields: returnOrderFields,
    initialData: {
      ...order,
      reference: undefined
    },
    modelType: ModelType.returnorder,
    follow: true
  });

  const issueOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.return_order_issue, order.pk),
    title: t`Issue Return Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Issue this order`,
    successMessage: t`Order issued`
  });

  const cancelOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.return_order_cancel, order.pk),
    title: t`Cancel Return Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Cancel this order`,
    successMessage: t`Order canceled`
  });

  const holdOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.return_order_hold, order.pk),
    title: t`Hold Return Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Place this order on hold`,
    successMessage: t`Order placed on hold`
  });

  const completeOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.return_order_complete, order.pk),
    title: t`Complete Return Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Mark this order as complete`,
    successMessage: t`Order completed`
  });

  const roStatus = useStatusCodes({ modelType: ModelType.returnorder });

  const orderActions = useMemo(() => {
    const canEdit: boolean = user.hasChangeRole(UserRoles.return_order);

    const canIssue: boolean =
      canEdit &&
      (order.status == roStatus.PENDING || order.status == roStatus.ON_HOLD);

    const canHold: boolean =
      canEdit &&
      (order.status == roStatus.PENDING ||
        order.status == roStatus.PLACED ||
        order.status == roStatus.IN_PROGRESS);

    const canCancel: boolean =
      canEdit &&
      (order.status == roStatus.PENDING ||
        order.status == roStatus.IN_PROGRESS ||
        order.status == roStatus.ON_HOLD);

    const canComplete: boolean =
      canEdit && order.status == roStatus.IN_PROGRESS;

    return [
      <PrimaryActionButton
        title={t`Issue Order`}
        icon="issue"
        hidden={!canIssue}
        color="blue"
        onClick={() => issueOrder.open()}
      />,
      <PrimaryActionButton
        title={t`Complete Order`}
        icon="complete"
        hidden={!canComplete}
        color="green"
        onClick={() => completeOrder.open()}
      />,
      <AdminButton model={ModelType.returnorder} pk={order.pk} />,
      <BarcodeActionDropdown
        model={ModelType.returnorder}
        pk={order.pk}
        hash={order?.barcode_hash}
      />,
      <PrintingActions
        modelType={ModelType.returnorder}
        items={[order.pk]}
        enableReports
      />,
      <OptionsActionDropdown
        tooltip={t`Order Actions`}
        actions={[
          EditItemAction({
            hidden: !user.hasChangeRole(UserRoles.return_order),
            tooltip: t`Edit order`,
            onClick: () => {
              editReturnOrder.open();
            }
          }),
          DuplicateItemAction({
            tooltip: t`Duplicate order`,
            hidden: !user.hasChangeRole(UserRoles.return_order),
            onClick: () => duplicateReturnOrder.open()
          }),
          HoldItemAction({
            tooltip: t`Hold order`,
            hidden: !canHold,
            onClick: () => holdOrder.open()
          }),
          CancelItemAction({
            tooltip: t`Cancel order`,
            hidden: !canCancel,
            onClick: () => cancelOrder.open()
          })
        ]}
      />
    ];
  }, [user, order, roStatus]);

  return (
    <>
      {editReturnOrder.modal}
      {issueOrder.modal}
      {cancelOrder.modal}
      {holdOrder.modal}
      {completeOrder.modal}
      {duplicateReturnOrder.modal}
      <InstanceDetail status={requestStatus} loading={instanceQuery.isFetching}>
        <Stack gap="xs">
          <PageDetail
            title={t`Return Order` + `: ${order.reference}`}
            subtitle={order.description}
            imageUrl={order.customer_detail?.image}
            badges={orderBadges}
            actions={orderActions}
            breadcrumbs={[{ name: t`Sales`, url: '/sales/' }]}
            editAction={editReturnOrder.open}
            editEnabled={user.hasChangePermission(ModelType.returnorder)}
          />
          <PanelGroup pageKey="returnorder" panels={orderPanels} />
        </Stack>
      </InstanceDetail>
    </>
  );
}
