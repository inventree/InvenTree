import { t } from '@lingui/macro';
import { LoadingOverlay, Skeleton, Stack } from '@mantine/core';
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

import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
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

  const orderPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'detail',
        label: t`Order Details`,
        icon: <IconInfoCircle />
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
          <BuildOrderTable
            params={{
              sales_order: order.pk
            }}
          />
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
