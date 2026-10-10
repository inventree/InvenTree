import { t } from '@lingui/core/macro';
import { Skeleton } from '@mantine/core';
import { IconPaperclip } from '@tabler/icons-react';

import type { ModelType } from '@lib/enums/ModelType';
import type { PanelType } from '@lib/types/Panel';
import { AttachmentTable } from '../../tables/general/AttachmentTable';

export default function AttachmentPanel({
  model_type,
  model_id,
  attachment_count
}: {
  model_type: ModelType;
  model_id: number | undefined;
  attachment_count?: number;
}): PanelType {
  return {
    name: 'attachments',
    label: t`Attachments`,
    icon: <IconPaperclip />,
    hotkey: 'mod+Shift+A',
    notification_dot: attachment_count ? 'info' : null,
    content:
      model_type && model_id ? (
        <AttachmentTable model_type={model_type} model_id={model_id} />
      ) : (
        <Skeleton />
      )
  };
}
