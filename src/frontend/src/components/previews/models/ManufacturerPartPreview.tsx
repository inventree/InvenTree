import { t } from '@lingui/core/macro';
import { ManufacturerPartDetailsPanel } from '../../../pages/company/ManufacturerPartDetailsPanel';
import type { PreviewType } from '../PreviewType';

export function ManufacturerPartPreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  const manufacturer =
    instance?.manufacturer_detail?.name ?? instance?.manufacturer_name;
  const mpn = instance?.MPN ?? `#${modelId}`;

  let title = `${t`Manufacturer Part`} ${mpn}`;

  if (manufacturer) {
    title += ` (${manufacturer})`;
  }

  return {
    title,
    preview: <ManufacturerPartDetailsPanel instance={instance} />
  };
}
