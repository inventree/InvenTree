import type { PreviewType } from '@lib/types/Preview';
import { t } from '@lingui/core/macro';
import { RepairOrderDetailsPanel } from '../../../pages/repair/RepairOrderDetailsPanel';

export function RepairOrderPreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  const customer = instance?.customer_detail?.name;
  const ref = instance?.reference ?? `#${modelId}`;

  let title = `${t`Repair Order`} ${ref}`;

  if (customer) {
    title += ` (${customer})`;
  }

  return {
    title,
    preview: <RepairOrderDetailsPanel instance={instance} />
  };
}
