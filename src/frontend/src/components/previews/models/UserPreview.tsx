import type { PreviewType } from '@lib/types/Preview';
import { t } from '@lingui/core/macro';
import { UserDetailsPanel } from '../../../pages/core/UserDetailsPanel';

export function UserPreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  return {
    title: `${t`User`} - ${instance?.username ?? `#${modelId}`}`,
    preview: <UserDetailsPanel instance={instance} />
  };
}
