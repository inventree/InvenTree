import type { PreviewType } from '@lib/types/Preview';
import { t } from '@lingui/core/macro';
import { SalesOrderDetailsPanel } from '../../../pages/sales/SalesOrderDetailsPanel';

export function SalesOrderPreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  const customer = instance?.customer_detail?.name ?? instance?.customer_name;
  const ref = instance?.reference ?? `#${modelId}`;

  let title = `${t`Sales Order`} ${ref}`;

  if (customer) {
    title += ` (${customer})`;
  }

  return {
    title,
    preview: <SalesOrderDetailsPanel instance={instance} />
  };
}
