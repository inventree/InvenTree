import type { PreviewType } from '@lib/types/Preview';
import { t } from '@lingui/core/macro';
import { LocationTypeDetailsPanel } from '../../../pages/stock/LocationTypeDetailsPanel';

export function StockLocationTypePreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  return {
    title: `${t`Stock Location Type`} - ${instance?.name ?? `#${modelId}`}`,
    preview: <LocationTypeDetailsPanel instance={instance} />
  };
}
