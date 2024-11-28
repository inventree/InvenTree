import { t } from '@lingui/macro';
import { Skeleton } from '@mantine/core';
import { IconPaperclip } from '@tabler/icons-react';

import type { ModelType } from '../../enums/ModelType';
import { AttachmentTable } from '../../tables/general/AttachmentTable';
import type { PanelType } from './Panel';

export default function AttachmentPanel({
  model_type,
  model_id
}: {
  model_type: ModelType;
  model_id: number | undefined;
}): PanelType {
  return {
    name: 'attachments',
    label: t`Attachments`,
    icon: <IconPaperclip />,
    content:
      model_type && model_id ? (
        <AttachmentTable model_type={model_type} model_id={model_id} />
      ) : (
        <Skeleton />
      )
  };
}
