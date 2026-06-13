import { t } from '@lingui/core/macro';
import { Skeleton } from '@mantine/core';
import { IconPaperclip } from '@tabler/icons-react';

import type { ModelType } from '@lib/enums/ModelType';
import { ApiEndpoints, apiUrl } from '@lib/index';
import type { PanelType } from '@lib/types/Panel';
import { api } from '../../App';
import { AttachmentTable } from '../../tables/general/AttachmentTable';

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
    hotkey: 'mod+Shift+A',
    notification_dot: async () => {
      if (!model_type || !model_id) {
        return null;
      }

      return api
        .get(apiUrl(ApiEndpoints.attachment_list), {
          params: {
            model_type: model_type,
            model_id: model_id,
            limit: 1
          }
        })
        .then((response) => ((response.data?.count ?? 0) > 0 ? 'info' : null));
    },
    content:
      model_type && model_id ? (
        <AttachmentTable model_type={model_type} model_id={model_id} />
      ) : (
        <Skeleton />
      )
  };
}
