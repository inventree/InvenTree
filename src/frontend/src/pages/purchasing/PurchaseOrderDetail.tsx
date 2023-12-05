import { t } from '@lingui/macro';
import { LoadingOverlay, Stack } from '@mantine/core';
import {
  IconDots,
  IconInfoCircle,
  IconList,
  IconNotes,
  IconPackages,
  IconPaperclip
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import {
  ActionDropdown,
  BarcodeActionDropdown,
  DeleteItemAction,
  EditItemAction,
  LinkBarcodeAction,
  UnlinkBarcodeAction,
  ViewBarcodeAction
} from '../../components/items/ActionDropdown';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { AttachmentTable } from '../../components/tables/general/AttachmentTable';
import { PurchaseOrderLineItemTable } from '../../components/tables/purchasing/PurchaseOrderLineItemTable';
import { StockItemTable } from '../../components/tables/stock/StockItemTable';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { ApiPaths } from '../../enums/ApiEndpoints';
import { useInstance } from '../../hooks/UseInstance';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';

/**
 * Detail page for a single PurchaseOrder
 */
export default function PurchaseOrderDetail() {
  const { id } = useParams();

  const user = useUserState();

  const { instance: order, instanceQuery } = useInstance({
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
        name: 'detail',
        label: t`Order Details`,
        icon: <IconInfoCircle />
      },
      {
        name: 'line-items',
        label: t`Line Items`,
        icon: <IconList />,
        content: order?.pk && <PurchaseOrderLineItemTable orderId={order.pk} />
      },
      {
        name: 'received-stock',
        label: t`Received Stock`,
        icon: <IconPackages />,
        content: (
          <StockItemTable
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

  const poActions = useMemo(() => {
    // TODO: Disable certain actions based on user permissions
    return [
      <BarcodeActionDropdown
        actions={[
          ViewBarcodeAction({}),
          LinkBarcodeAction({
            disabled: order?.barcode_hash
          }),
          UnlinkBarcodeAction({
            disabled: !order?.barcode_hash
          })
        ]}
      />,
      <ActionDropdown
        key="order-actions"
        tooltip={t`Order Actions`}
        icon={<IconDots />}
        actions={[EditItemAction({}), DeleteItemAction({})]}
      />
    ];
  }, [id, order, user]);

  return (
    <>
      <Stack spacing="xs">
        <LoadingOverlay visible={instanceQuery.isFetching} />
        <PageDetail
          title={t`Purchase Order` + `: ${order.reference}`}
          subtitle={order.description}
          imageUrl={order.supplier_detail?.image}
          breadcrumbs={[{ name: t`Purchasing`, url: '/purchasing/' }]}
          actions={poActions}
        />
        <PanelGroup pageKey="purchaseorder" panels={orderPanels} />
      </Stack>
    </>
  );
}
