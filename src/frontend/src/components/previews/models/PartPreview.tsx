import type { PreviewType } from '@lib/types/Preview';
import { PartDetailsPanel } from '../../../pages/part/PartDetailsPanel';

export function PartPreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  return {
    title: instance?.full_name || instance?.name || `Part #${modelId}`,
    preview: <PartDetailsPanel instance={instance} />
  };
}
