import type { PreviewType } from '@lib/types/Preview';
import { t } from '@lingui/core/macro';
import { PurchaseOrderDetailsPanel } from '../../../pages/purchasing/PurchaseOrderDetailsPanel';

export function PurchaseOrderPreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  const supplier = instance?.supplier_detail?.name ?? instance?.supplier_name;
  const ref = instance?.reference ?? `#${modelId}`;

  let title = `${t`Purchase Order`} ${ref}`;

  if (supplier) {
    title += ` (${supplier})`;
  }

  return {
    title: title,
    preview: <PurchaseOrderDetailsPanel instance={instance} />
  };
}
