import { t } from '@lingui/core/macro';
import { CompanyDetailsPanel } from '../../../pages/company/CompanyDetailsPanel';
import type { PreviewType } from '../PreviewType';

export function CompanyPreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  const name = instance?.name ?? `#${modelId}`;

  return {
    title: `${t`Company`} - ${name}`,
    preview: <CompanyDetailsPanel instance={instance} />
  };
}
