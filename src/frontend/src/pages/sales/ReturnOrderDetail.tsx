import { t } from '@lingui/core/macro';
import { Accordion, Grid, Skeleton, Stack, Text } from '@mantine/core';
import { IconInfoCircle, IconList } from '@tabler/icons-react';
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
import { RenderAddress } from '../../components/render/Company';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import { formatCurrency } from '../../defaults/formatters';
import { useReturnOrderFields } from '../../forms/ReturnOrderForms';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
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
    refreshInstance
  } = useInstance({
    endpoint: ApiEndpoints.return_order_list,
    pk: id,
    params: {
      customer_detail: true
    }
  });

  const roStatus = useStatusCodes({ modelType: ModelType.returnorder });

  const orderOpen = useMemo(() => {
    return (
      order.status == roStatus.PENDING ||
      order.status == roStatus.PLACED ||
      order.status == roStatus.IN_PROGRESS ||
      order.status == roStatus.ON_HOLD
    );
  }, [order, roStatus]);

  const lineItemsEditable: boolean = useMemo(() => {
    if (orderOpen) {
      return true;
    } else {
      return globalSettings.isSet('RETURNORDER_EDIT_COMPLETED_ORDERS');
    }
  }, [orderOpen, globalSettings]);

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
        icon: 'customer',
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
      },
      {
        type: 'status',
        name: 'status_custom_key',
        label: t`Custom Status`,
        model: ModelType.returnorder,
        icon: 'status',
        hidden:
          !order.status_custom_key || order.status_custom_key == order.status
      }
    ];

    const tr: DetailsField[] = [
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
            currency: order?.order_currency || order?.customer_detail?.currency
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
        name: 'address',
        label: t`Return Address`,
        icon: 'address',
        value_formatter: () =>
          order.address_detail ? (
            <RenderAddress instance={order.address_detail} />
          ) : (
            <Text size='sm' c='red'>{t`Not specified`}</Text>
          )
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
        icon: 'calendar',
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
        copy: true,
        hidden: !order.start_date
      },
      {
        type: 'date',
        name: 'target_date',
        label: t`Target Date`,
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
            <Accordion.Item value='line-items' key='lineitems'>
              <Accordion.Control>
                <StylishText size='lg'>{t`Line Items`}</StylishText>
              </Accordion.Control>
              <Accordion.Panel>
                <ReturnOrderLineItemTable
                  orderId={order.pk}
                  order={order}
                  orderDetailRefresh={refreshInstance}
                  customerId={order.customer}
                  editable={lineItemsEditable}
                  currency={orderCurrency}
                />
              </Accordion.Panel>
            </Accordion.Item>
            <Accordion.Item value='extra-items' key='extraitems'>
              <Accordion.Control>
                <StylishText size='lg'>{t`Extra Line Items`}</StylishText>
              </Accordion.Control>
              <Accordion.Panel>
                <ExtraLineItemTable
                  endpoint={ApiEndpoints.return_order_extra_line_list}
                  orderId={order.pk}
                  orderDetailRefresh={refreshInstance}
                  currency={orderCurrency}
                  editable={lineItemsEditable}
                  role={UserRoles.return_order}
                />
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>
        )
      },
      ParametersPanel({
        model_type: ModelType.returnorder,
        model_id: order.pk
      }),
      AttachmentPanel({
        model_type: ModelType.returnorder,
        model_id: order.pk
      }),
      NotesPanel({
        model_type: ModelType.returnorder,
        model_id: order.pk,
        has_note: !!order.notes
      })
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

  const returnOrderFields = useReturnOrderFields({});

  const duplicateReturnOrderFields = useReturnOrderFields({
    duplicateOrderId: order.pk
  });

  const editReturnOrder = useEditApiFormModal({
    url: ApiEndpoints.return_order_list,
    pk: order.pk,
    title: t`Edit Return Order`,
    fields: returnOrderFields,
    onFormSuccess: () => {
      refreshInstance();
    }
  });

  const duplicateReturnOrderInitialData = useMemo(() => {
    const data = { ...order };
    // if we set the reference to null/undefined, it will be left blank in the form
    // if we omit the reference altogether, it will be auto-generated via reference pattern
    // from the OPTIONS response
    delete data.reference;
    return data;
  }, [order]);

  const duplicateReturnOrder = useCreateApiFormModal({
    url: ApiEndpoints.return_order_list,
    title: t`Add Return Order`,
    fields: duplicateReturnOrderFields,
    initialData: duplicateReturnOrderInitialData,
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
    successMessage: t`Order cancelled`
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
        icon='issue'
        hidden={!canIssue}
        color='blue'
        onClick={() => issueOrder.open()}
      />,
      <PrimaryActionButton
        title={t`Complete Order`}
        icon='complete'
        hidden={!canComplete}
        color='green'
        onClick={() => completeOrder.open()}
      />,
      <AdminButton model={ModelType.returnorder} id={order.pk} />,
      <BarcodeActionDropdown
        model={ModelType.returnorder}
        pk={order.pk}
        hash={order?.barcode_hash}
      />,
      <PrintingActions
        modelType={ModelType.returnorder}
        items={[order.pk]}
        enableReports
        enableLabels
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
  }, [user, order, orderOpen, roStatus]);

  const subtitle: string = useMemo(() => {
    let t = order.customer_detail?.name || '';

    if (order.customer_reference) {
      t += ` (${order.customer_reference})`;
    }

    return t;
  }, [order]);

  return (
    <>
      {editReturnOrder.modal}
      {issueOrder.modal}
      {cancelOrder.modal}
      {holdOrder.modal}
      {completeOrder.modal}
      {duplicateReturnOrder.modal}
      <InstanceDetail
        query={instanceQuery}
        requiredRole={UserRoles.return_order}
      >
        <Stack gap='xs'>
          <PageDetail
            title={`${t`Return Order`}: ${order.reference}`}
            subtitle={subtitle}
            imageUrl={order.customer_detail?.image}
            badges={orderBadges}
            actions={orderActions}
            breadcrumbs={[{ name: t`Sales`, url: '/sales/' }]}
            lastCrumb={[
              { name: order.reference, url: `/sales/return-order/${order.pk}` }
            ]}
            editAction={editReturnOrder.open}
            editEnabled={user.hasChangePermission(ModelType.returnorder)}
          />
          <PanelGroup
            pageKey='returnorder'
            panels={orderPanels}
            model={ModelType.returnorder}
            reloadInstance={instanceQuery.refetch}
            instance={order}
            id={order.pk}
          />
        </Stack>
      </InstanceDetail>
    </>
  );
}
