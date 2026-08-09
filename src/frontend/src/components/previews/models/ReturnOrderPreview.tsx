import type { PreviewType } from '@lib/types/Preview';
import { t } from '@lingui/core/macro';
import { ReturnOrderDetailsPanel } from '../../../pages/sales/ReturnOrderDetailsPanel';

export function ReturnOrderPreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  const customer = instance?.customer_detail?.name ?? instance?.customer_name;
  const ref = instance?.reference ?? `#${modelId}`;

  let title = `${t`Return Order`} ${ref}`;

  if (customer) {
    title += ` (${customer})`;
  }

  return {
    title,
    preview: <ReturnOrderDetailsPanel instance={instance} />
  };
}
