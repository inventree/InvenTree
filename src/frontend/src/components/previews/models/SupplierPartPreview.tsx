import { t } from '@lingui/core/macro';
import { SupplierPartDetailsPanel } from '../../../pages/company/SupplierPartDetailsPanel';
import type { PreviewType } from '../PreviewType';

export function SupplierPartPreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  const supplier = instance?.supplier_detail?.name ?? instance?.supplier_name;
  const sku = instance?.SKU ?? `#${modelId}`;

  let title = `${t`Supplier Part`} ${sku}`;

  if (supplier) {
    title += ` (${supplier})`;
  }

  return {
    title,
    preview: <SupplierPartDetailsPanel instance={instance} />
  };
}
