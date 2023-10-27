import { t } from '@lingui/macro';
import { LoadingOverlay, Stack } from '@mantine/core';
import {
  IconList,
  IconNote,
  IconNotes,
  IconPackages,
  IconPaperclip
} from '@tabler/icons-react';
import React, { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { AttachmentTable } from '../../components/tables/general/AttachmentTable';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { useInstance } from '../../hooks/UseInstance';
import { ApiPaths, apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';

/**
 * Detail page for a single PurchaseOrder
 */
export default function PurchaseOrderDetail() {
  const { id } = useParams();

  const user = useUserState();

  const {
    instance: order,
    refreshInstance,
    instanceQuery
  } = useInstance({
    endpoint: ApiPaths.purchase_order_list,
    pk: id,
    params: {
      supplier_detail: true
    },
    refetchOnMount: true
  });

  const orderPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'line-items',
        label: t`Line Items`,
        icon: <IconList />
      },
      {
        name: 'received-stock',
        label: t`Received Stock`,
        icon: <IconPackages />
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip />,
        content: (
          <AttachmentTable
            endpoint={ApiPaths.purchase_order_attachment_list}
            model="order"
            pk={order.pk ?? -1}
          />
        )
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes />,
        content: (
          <NotesEditor
            url={apiUrl(ApiPaths.purchase_order_list, order.pk)}
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
          title={t`Purchase Order` + `: ${order.reference}`}
          subtitle={order.description}
          imageUrl={order.supplier_detail?.image}
          breadcrumbs={[{ name: t`Purchasing`, url: '/purchasing/' }]}
        />
        <PanelGroup pageKey="purchaseorder" panels={orderPanels} />
      </Stack>
    </>
  );
}
