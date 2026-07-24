import { t } from '@lingui/core/macro';
import { Accordion, Grid, Skeleton, Stack } from '@mantine/core';
import { IconInfoCircle, IconList } from '@tabler/icons-react';
import { type ReactNode, useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { StylishText } from '@lib/components/StylishText';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { PanelType } from '@lib/types/Panel';
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
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import AttachmentPanel from '../../components/panels/AttachmentPanel';
import NotesPanel from '../../components/panels/NotesPanel';
import { PanelGroup } from '../../components/panels/PanelGroup';
import ParametersPanel from '../../components/panels/ParametersPanel';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import { useRepairOrderFields } from '../../forms/RepairOrderForms';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import RepairOrderLineItemTable from '../../tables/sales/RepairOrderLineItemTable';

export default function RepairOrderDetail() {
  const { id } = useParams();
  const user = useUserState();
  const globalSettings = useGlobalSettingsState();

  const {
    instance: order,
    instanceQuery,
    refreshInstance
  } = useInstance({
    endpoint: ApiEndpoints.repair_order_list,
    pk: id,
    params: {
      customer_detail: true,
      asset_detail: true
    }
  });

  const roStatus = useStatusCodes({ modelType: ModelType.repairorder });

  const orderOpen = useMemo(() => {
    return (
      order.status == roStatus.PENDING ||
      order.status == roStatus.IN_PROGRESS ||
      order.status == roStatus.ON_HOLD
    );
  }, [order, roStatus]);

  const lineItemsEditable: boolean = useMemo(() => {
    return (
      orderOpen || globalSettings.isSet('RETURNORDER_EDIT_COMPLETED_ORDERS')
    );
  }, [orderOpen, globalSettings]);

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
        type: 'link',
        name: 'customer',
        icon: 'customers',
        label: t`Customer`,
        model: ModelType.company
      },
      {
        type: 'link',
        name: 'asset',
        icon: 'part',
        label: t`Fixed Asset`,
        model: ModelType.stockitem
      },
      {
        type: 'text',
        name: 'description',
        label: t`Description`,
        copy: true
      },
      {
        type: 'text',
        name: 'symptoms',
        label: t`Symptoms`,
        copy: true,
        hidden: !order.symptoms
      },
      {
        type: 'status',
        name: 'status',
        label: t`Status`,
        model: ModelType.repairorder
      },
      {
        type: 'status',
        name: 'status_custom_key',
        label: t`Custom Status`,
        model: ModelType.repairorder,
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
      }
    ];

    return (
      <ItemDetailsGrid>
        <Grid grow>
          <DetailsImage
            appRole={UserRoles.repair_order}
            apiPath={ApiEndpoints.company_list}
            src={order.customer_detail?.image}
            pk={order.customer}
          />
          <Grid.Col span={{ base: 12, sm: 8 }}>
            <DetailsTable fields={tl} item={order} />
          </Grid.Col>
        </Grid>
        <DetailsTable fields={tr} item={order} />
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
          <Accordion multiple={true} defaultValue={['line-items']}>
            <Accordion.Item value='line-items' key='lineitems'>
              <Accordion.Control>
                <StylishText size='lg'>{t`Line Items`}</StylishText>
              </Accordion.Control>
              <Accordion.Panel>
                <RepairOrderLineItemTable
                  orderId={order.pk}
                  order={order}
                  orderDetailRefresh={refreshInstance}
                  editable={lineItemsEditable}
                />
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>
        )
      },
      ParametersPanel({
        model_type: ModelType.repairorder,
        model_id: order.pk
      }),
      AttachmentPanel({
        model_type: ModelType.repairorder,
        model_id: order.pk
      }),
      NotesPanel({
        model_type: ModelType.repairorder,
        model_id: order.pk,
        has_note: !!order.notes
      })
    ];
  }, [order, id, user, lineItemsEditable]);

  const orderBadges: ReactNode[] = useMemo(() => {
    return instanceQuery.isLoading
      ? []
      : [
          <StatusRenderer
            status={order.status_custom_key}
            type={ModelType.repairorder}
            options={{ size: 'lg' }}
          />
        ];
  }, [order, instanceQuery]);

  const repairOrderFields = useRepairOrderFields({});

  const duplicateRepairOrderFields = useRepairOrderFields({
    duplicateOrderId: order.pk
  });

  const editRepairOrder = useEditApiFormModal({
    url: ApiEndpoints.repair_order_list,
    pk: order.pk,
    title: t`Edit Repair Order`,
    fields: repairOrderFields,
    onFormSuccess: () => {
      refreshInstance();
    }
  });

  const duplicateRepairOrderInitialData = useMemo(() => {
    const data = { ...order };
    delete data.reference;
    return data;
  }, [order]);

  const duplicateRepairOrder = useCreateApiFormModal({
    url: ApiEndpoints.repair_order_list,
    title: t`Add Repair Order`,
    fields: duplicateRepairOrderFields,
    initialData: duplicateRepairOrderInitialData,
    modelType: ModelType.repairorder,
    follow: true
  });

  const issueOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.repair_order_issue, order.pk),
    title: t`Issue Repair Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Issue this order`,
    successMessage: t`Order issued`
  });

  const cancelOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.repair_order_cancel, order.pk),
    title: t`Cancel Repair Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Cancel this order`,
    successMessage: t`Order cancelled`
  });

  const holdOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.repair_order_hold, order.pk),
    title: t`Hold Repair Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Place this order on hold`,
    successMessage: t`Order placed on hold`
  });

  const completeOrder = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.repair_order_complete, order.pk),
    title: t`Complete Repair Order`,
    onFormSuccess: refreshInstance,
    preFormWarning: t`Mark this order as complete`,
    successMessage: t`Order completed`
  });

  const orderActions = useMemo(() => {
    const canEdit: boolean = user.hasChangeRole(UserRoles.repair_order);

    const canIssue: boolean =
      canEdit &&
      (order.status == roStatus.PENDING || order.status == roStatus.ON_HOLD);

    const canHold: boolean =
      canEdit &&
      (order.status == roStatus.PENDING ||
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
      <AdminButton model={ModelType.repairorder} id={order.pk} />,
      <BarcodeActionDropdown
        model={ModelType.repairorder}
        pk={order.pk}
        hash={order?.barcode_hash}
      />,
      <PrintingActions
        modelType={ModelType.repairorder}
        items={[order.pk]}
        enableReports
        enableLabels
      />,
      <OptionsActionDropdown
        tooltip={t`Order Actions`}
        actions={[
          EditItemAction({
            hidden: !user.hasChangeRole(UserRoles.repair_order),
            tooltip: t`Edit order`,
            onClick: () => {
              editRepairOrder.open();
            }
          }),
          DuplicateItemAction({
            tooltip: t`Duplicate order`,
            hidden: !user.hasChangeRole(UserRoles.repair_order),
            onClick: () => duplicateRepairOrder.open()
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

  const subtitle: string = useMemo(() => {
    return order.customer_detail?.name || '';
  }, [order]);

  return (
    <>
      {editRepairOrder.modal}
      {issueOrder.modal}
      {cancelOrder.modal}
      {holdOrder.modal}
      {completeOrder.modal}
      {duplicateRepairOrder.modal}
      <InstanceDetail
        query={instanceQuery}
        requiredRole={UserRoles.repair_order}
      >
        <Stack gap='xs'>
          <PageDetail
            title={`${t`Repair Order`}: ${order.reference}`}
            subtitle={subtitle}
            imageUrl={order.customer_detail?.image}
            badges={orderBadges}
            actions={orderActions}
            breadcrumbs={[{ name: t`Sales`, url: '/sales/' }]}
            lastCrumb={[
              { name: order.reference, url: `/sales/repair-order/${order.pk}` }
            ]}
            editAction={editRepairOrder.open}
            editEnabled={user.hasChangePermission(ModelType.repairorder)}
          />
          <PanelGroup
            pageKey='repairorder'
            panels={orderPanels}
            model={ModelType.repairorder}
            reloadInstance={instanceQuery.refetch}
            instance={order}
            id={order.pk}
          />
        </Stack>
      </InstanceDetail>
    </>
  );
}
