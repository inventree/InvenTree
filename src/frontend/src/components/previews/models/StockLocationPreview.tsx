import { t } from '@lingui/core/macro';
import { StockLocationDetailsPanel } from '../../../pages/stock/StockLocationDetailsPanel';
import type { PreviewType } from '../PreviewType';

export function StockLocationPreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  const name = `${t`Stock Location`} - ${instance?.name ?? `#${modelId}`}`;

  return {
    title: name,
    preview: <StockLocationDetailsPanel instance={instance} />
  };
}
