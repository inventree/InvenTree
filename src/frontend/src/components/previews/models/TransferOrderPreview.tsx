import { t } from '@lingui/core/macro';
import { TransferOrderDetailsPanel } from '../../../pages/stock/TransferOrderDetailsPanel';
import type { PreviewType } from '../PreviewType';

export function TransferOrderPreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  const ref = instance?.reference ?? `#${modelId}`;

  return {
    title: `${t`Transfer Order`} ${ref}`,
    preview: <TransferOrderDetailsPanel instance={instance} />
  };
}
