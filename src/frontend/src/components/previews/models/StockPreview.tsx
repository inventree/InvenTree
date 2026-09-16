import { formatDecimal } from '@lib/functions/Formatting';
import type { PreviewType } from '@lib/types/Preview';
import { StockDetailsPanel } from '../../../pages/stock/StockDetailsPanel';

export function StockPreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  const part = instance?.part_detail;

  let title = `Stock Item #${modelId}`;

  if (part) {
    title = part?.full_name ?? part?.name;

    if (instance.serial) {
      title += ` (# ${instance.serial})`;
    } else {
      title += ` (x ${formatDecimal(instance.quantity)})`;
    }
  }

  return {
    title: title,
    preview: <StockDetailsPanel instance={instance} />
  };
}
