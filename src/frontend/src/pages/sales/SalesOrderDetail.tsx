import { t } from '@lingui/macro';
import { Grid, LoadingOverlay, Skeleton, Stack } from '@mantine/core';
import {
  IconInfoCircle,
  IconList,
  IconNotes,
  IconPaperclip,
  IconTools,
  IconTruckDelivery,
  IconTruckLoading
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { DetailsField, DetailsTable } from '../../components/details/Details';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useInstance } from '../../hooks/UseInstance';
import { apiUrl } from '../../states/ApiState';
import { BuildOrderTable } from '../../tables/build/BuildOrderTable';
import { AttachmentTable } from '../../tables/general/AttachmentTable';

/**
 * Detail page for a single SalesOrder
 */
export default function SalesOrderDetail() {
  const { id } = useParams();

  const { instance: order, instanceQuery } = useInstance({
    endpoint: ApiEndpoints.sales_order_list,
    pk: id,
    params: {
      customer_detail: true
    }
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
        model: ModelType.salesorder
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
        // TODO: Fix this progress bar
      },
      {
        type: 'text',
        name: 'currency',
        label: t`Order Currency,`
      },
      {
        type: 'text',
        name: 'total_cost',
        label: t`Total Cost`
        // TODO: Implement this!
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
        copy: true
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
        icon: <IconList />
      },
      {
        name: 'pending-shipments',
        label: t`Pending Shipments`,
        icon: <IconTruckLoading />
      },
      {
        name: 'completed-shipments',
        label: t`Completed Shipments`,
        icon: <IconTruckDelivery />
      },
      {
        name: 'build-orders',
        label: t`Build Orders`,
        icon: <IconTools />,
        content: order?.pk ? (
          <BuildOrderTable salesOrderId={order.pk} />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip />,
        content: (
          <AttachmentTable
            endpoint={ApiEndpoints.sales_order_attachment_list}
            model="order"
            pk={Number(id)}
          />
        )
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes />,
        content: (
          <NotesEditor
            url={apiUrl(ApiEndpoints.sales_order_list, id)}
            data={order.notes ?? ''}
            allowEdit={true}
          />
        )
      }
    ];
  }, [order, id]);

  return (
    <>
      <Stack spacing="xs">
        <LoadingOverlay visible={instanceQuery.isFetching} />
        <PageDetail
          title={t`Sales Order` + `: ${order.reference}`}
          subtitle={order.description}
          imageUrl={order.customer_detail?.image}
          breadcrumbs={[{ name: t`Sales`, url: '/sales/' }]}
        />
        <PanelGroup pageKey="salesorder" panels={orderPanels} />
      </Stack>
    </>
  );
}
