import { t } from '@lingui/core/macro';
import { Grid, Skeleton, Stack } from '@mantine/core';
import { type ReactNode, useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { IconInfoCircle } from '@tabler/icons-react';
import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import AttachmentPanel from '../../components/panels/AttachmentPanel';
import NotesPanel from '../../components/panels/NotesPanel';
import type { PanelType } from '../../components/panels/Panel';
import { PanelGroup } from '../../components/panels/PanelGroup';
import ParametersPanel from '../../components/panels/ParametersPanel';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import { useInstance } from '../../hooks/UseInstance';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';

export default function TransferOrderDetail() {
  const { id } = useParams();

  const user = useUserState();

  const globalSettings = useGlobalSettingsState();

  const {
    instance: order,
    instanceQuery,
    refreshInstance
  } = useInstance({
    endpoint: ApiEndpoints.transfer_order_list,
    pk: id,
    params: {}
  });

  const toStatus = useStatusCodes({ modelType: ModelType.transferorder });

  const orderOpen = useMemo(() => {
    return (
      order.status == toStatus.PENDING ||
      order.status == toStatus.ISSUED ||
      order.status == toStatus.ON_HOLD
    );
  }, [order, toStatus]);

  // TODO: does this make any sense for Transfer Orders???
  //   const lineItemsEditable: boolean = useMemo(() => {
  //     if (orderOpen) {
  //       return true;
  //     } else {
  //       return globalSettings.isSet('TRANSFERORDER_EDIT_COMPLETED_ORDERS');
  //     }
  //   }, [orderOpen, globalSettings]);

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
        name: 'take_from',
        icon: 'location',
        label: t`Source Location`,
        model: ModelType.stocklocation
      },
      {
        type: 'link',
        name: 'destination',
        icon: 'location',
        label: t`Destination Location`,
        model: ModelType.stocklocation,
        hidden: !order.destination
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
        model: ModelType.transferorder
      },
      {
        type: 'status',
        name: 'status_custom_key',
        label: t`Custom Status`,
        model: ModelType.transferorder,
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
          {/* TODO: what image do we show for a Transfer Order? */}
          {/* <DetailsImage
                        appRole={UserRoles.transfer_order}
                        apiPath={ApiEndpoints.transfer_order_list}
                        src="/static/img/blank_image.png"
                        pk={order.pk}
                    /> */}
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
      ParametersPanel({
        model_type: ModelType.transferorder,
        model_id: order.pk
      }),
      AttachmentPanel({
        model_type: ModelType.transferorder,
        model_id: order.pk
      }),
      NotesPanel({
        model_type: ModelType.transferorder,
        model_id: order.pk
      })
    ];
  }, [order, id, user]);

  const orderBadges: ReactNode[] = useMemo(() => {
    return instanceQuery.isLoading
      ? []
      : [
          <StatusRenderer
            status={order.status_custom_key}
            type={ModelType.transferorder}
            options={{ size: 'lg' }}
          />
        ];
  }, [order, instanceQuery]);

  const orderActions = useMemo(() => {
    return [];
  }, [user, order, orderOpen, toStatus]);

  const subtitle: string = useMemo(() => {
    const t = order.take_from_detail?.pathstring || '';
    const d = order.destination_detail?.pathstring || '';
    return `${t} → ${d}`;
  }, [order]);

  return (
    <>
      {/* {editReturnOrder.modal} */}
      {/* {issueOrder.modal} */}
      {/* {cancelOrder.modal} */}
      {/* {holdOrder.modal} */}
      {/* {completeOrder.modal} */}
      {/* {duplicateReturnOrder.modal} */}
      <InstanceDetail
        query={instanceQuery}
        requiredRole={UserRoles.transfer_order}
      >
        <Stack gap='xs'>
          <PageDetail
            title={`${t`Transfer Order`}: ${order.reference}`}
            subtitle={subtitle}
            // imageUrl={order.customer_detail?.image}
            badges={orderBadges}
            actions={orderActions}
            breadcrumbs={[{ name: t`Stock`, url: '/stock/' }]}
            lastCrumb={[
              {
                name: order.reference,
                url: `/stock/transfer-order/${order.pk}`
              }
            ]}
            // editAction={editReturnOrder.open}
            editEnabled={user.hasChangePermission(ModelType.transferorder)}
          />
          <PanelGroup
            pageKey='transferorder'
            panels={orderPanels}
            model={ModelType.transferorder}
            reloadInstance={instanceQuery.refetch}
            instance={order}
            id={order.pk}
          />
        </Stack>
      </InstanceDetail>
    </>
  );
}
