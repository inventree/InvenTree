import type { PreviewType } from '@lib/types/Preview';
import { t } from '@lingui/core/macro';
import { NonConformanceDetailsPanel } from '../../../pages/build/NonConformanceDetailsPanel';

export function NonConformancePreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  const ref = instance?.reference ?? `#${modelId}`;

  return {
    title: `${t`NCR`} ${ref}`,
    preview: <NonConformanceDetailsPanel instance={instance} />
  };
}
