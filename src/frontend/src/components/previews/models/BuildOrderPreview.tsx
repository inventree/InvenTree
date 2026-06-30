import { t } from '@lingui/core/macro';
import { BuildOrderDetailsPanel } from '../../../pages/build/BuildOrderDetailsPanel';
import type { PreviewType } from '../PreviewType';

export function BuildOrderPreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  const part = instance?.part_detail?.full_name ?? instance?.part_detail?.name;
  const ref = instance?.reference ?? `#${modelId}`;

  let title = `${t`Build Order`} ${ref}`;

  if (part) {
    title += ` (${part})`;
  }

  return {
    title,
    preview: <BuildOrderDetailsPanel instance={instance} />
  };
}
