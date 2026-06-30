import { t } from '@lingui/core/macro';
import { SalesOrderShipmentDetailsPanel } from '../../../pages/sales/SalesOrderShipmentDetailsPanel';
import type { PreviewType } from '../PreviewType';

export function SalesOrderShipmentPreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  const order = instance?.order_detail?.reference;
  const ref = instance?.reference ?? `#${modelId}`;

  let title = `${t`Shipment`} ${ref}`;

  if (order) {
    title += ` (${order})`;
  }

  return {
    title,
    preview: <SalesOrderShipmentDetailsPanel instance={instance} />
  };
}
