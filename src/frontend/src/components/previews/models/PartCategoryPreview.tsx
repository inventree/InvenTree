import type { PreviewType } from '@lib/types/Preview';
import { t } from '@lingui/core/macro';
import { PartCategoryDetailsPanel } from '../../../pages/part/PartCategoryDetailsPanel';

export function PartCategoryPreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  const name = `${t`Part Category`} - ${instance?.name ?? `#${modelId}`}`;

  return {
    title: name,
    preview: <PartCategoryDetailsPanel instance={instance} />
  };
}
