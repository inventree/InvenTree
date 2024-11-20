import { t } from '@lingui/macro';
import { Skeleton } from '@mantine/core';
import { IconNotes } from '@tabler/icons-react';

import type { ModelType } from '../../enums/ModelType';
import { useUserState } from '../../states/UserState';
import NotesEditor from '../editors/NotesEditor';
import type { PanelType } from './Panel';

export default function NotesPanel({
  model_type,
  model_id,
  editable
}: {
  model_type: ModelType;
  model_id: number | undefined;
  editable?: boolean;
}): PanelType {
  const user = useUserState.getState();

  return {
    name: 'notes',
    label: t`Notes`,
    icon: <IconNotes />,
    content:
      model_type && model_id ? (
        <NotesEditor
          modelType={model_type}
          modelId={model_id}
          editable={editable ?? user.hasChangePermission(model_type)}
        />
      ) : (
        <Skeleton />
      )
  };
}
