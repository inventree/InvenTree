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
import { getDetailUrl } from '@lib/functions/Navigation';
import type { PanelType } from '@lib/types/Panel';
import AdminButton from '../../components/buttons/AdminButton';
import PrimaryActionButton from '../../components/buttons/PrimaryActionButton';
import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import {
  CancelItemAction,
  DuplicateItemAction,
  EditItemAction,
  HoldItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/panels/PanelGroup';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import { useRepairOrderFields } from '../../forms/RepairOrderForms';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useModelFeatureActions } from '../../hooks/UseModelFeatureActions';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { useUserState } from '../../states/UserState';
import RepairOrderLineItemTable from '../../tables/sales/RepairOrderLineItemTable';

export default function RepairOrderDetail() {
  const { id } = useParams();
  const user = useUserState();

  const {
    instance: order,
    instanceQuery,
    refreshInstance
  } = useInstance({
    endpoint: ApiEndpoints.repair_order_list,
    pk: id,
    params: {
      customer_detail: true,
      part_detail: true,
      tags: true
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

  const lineItemsEditable: boolean = orderOpen;

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
        name: 'part',
        icon: 'part',
        label: t`Part`,
        model: ModelType.part,
        hidden: !order.part
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
        type: 'link',
        name: 'customer',
        icon: 'customers',
        label: t`Customer`,
        model: ModelType.company,
        hidden: !order.customer
      }
    ];

    const bl: DetailsField[] = [
      {
        type: 'text',
        name: 'issued_by',
        label: t`Issued By`,
        icon: 'user',
        badge: 'user',
        hidden: !order.issued_by
      },
      {
        type: 'text',
        name: 'completed_by',
        label: t`Completed By`,
        icon: 'user',
        badge: 'user',
        hidden: !order.completed_by
      },
      {
        type: 'text',
        name: 'responsible',
        label: t`Responsible`,
        badge: 'owner',
        hidden: !order.responsible
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
        type: 'link',
        name: 'take_from',
        icon: 'location',
        model: ModelType.stocklocation,
        model_formatter: (location: any) =>
          location?.description
            ? `${location.name} - ${location.description}`
            : location?.name,
        label: t`Source Location`,
        hidden: !order.take_from
      }
    ];

    const br: DetailsField[] = [
      {
        type: 'date',
        name: 'creation_date',
        label: t`Created`,
        icon: 'calendar',
        copy: true,
        hidden: !order.creation_date
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
        name: 'completion_date',
        label: t`Completed`,
        icon: 'calendar',
        copy: true,
        hidden: !order.completion_date
      }
    ];

    return (
      <ItemDetailsGrid
        tables={[
          { fields: tr, item: order },
          { fields: bl, item: order },
          { fields: br, item: order }
        ]}
      >
        <Grid grow>
          <DetailsImage
            apiPath={apiUrl(ApiEndpoints.part_list, order.part)}
            src={order.part_detail?.image ?? order.part_detail?.thumbnail}
            pk={order.part}
          />
          <Grid.Col span={{ base: 12, sm: 8 }}>
            <DetailsTable fields={tl} item={order} />
          </Grid.Col>
        </Grid>
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
                  assemblyPartId={order.part}
                  orderDetailRefresh={refreshInstance}
                  editable={lineItemsEditable}
                  sourceLocation={order.take_from}
                />
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>
        )
      }
    ];
  }, [order, id, user, lineItemsEditable, detailsPanel, refreshInstance]);

  const orderBadges: ReactNode[] = useMemo(() => {
    return instanceQuery.isLoading
      ? []
      : [
          <StatusRenderer
            status={order.status_custom_key || order.status}
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
    queryParams: new URLSearchParams({ tags: 'true' }),
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

  const featureActions = useModelFeatureActions({
    model: ModelType.repairorder,
    instance: order
  });

  const orderActions = useMemo(() => {
    const canEdit: boolean =
      orderOpen && user.hasChangeRole(UserRoles.repair_order);

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
      ...featureActions,
      <OptionsActionDropdown
        tooltip={t`Order Actions`}
        actions={[
          EditItemAction({
            hidden: !canEdit,
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
  }, [featureActions, user, order, roStatus, orderOpen]);

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
            breadcrumbs={[{ name: t`Manufacturing`, url: '/manufacturing' }]}
            lastCrumb={[
              {
                name: order.reference,
                url: getDetailUrl(ModelType.repairorder, order.pk)
              }
            ]}
            editAction={editRepairOrder.open}
            editEnabled={
              orderOpen && user.hasChangePermission(ModelType.repairorder)
            }
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
