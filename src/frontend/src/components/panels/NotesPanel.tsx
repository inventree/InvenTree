import type { ModelType } from '@lib/enums/ModelType';
import type { PanelType } from '@lib/types/Panel';
import { t } from '@lingui/core/macro';
import { Skeleton } from '@mantine/core';
import { IconNotes } from '@tabler/icons-react';
import { lazy } from 'react';
import { useUserState } from '../../states/UserState';

const NotesEditor = lazy(() => import('../editors/NotesEditor'));

export default function NotesPanel({
  model_type,
  model_id,
  editable,
  has_note
}: {
  model_type: ModelType;
  model_id: number | undefined;
  editable?: boolean;
  has_note?: boolean;
}): PanelType {
  const user = useUserState.getState();

  return {
    name: 'notes',
    label: t`Notes`,
    icon: <IconNotes />,
    hotkey: 'mod+Shift+N',
    notification_dot: has_note ? 'info' : null,
    content:
      model_type && model_id ? (
        <NotesEditor
          modelType={model_type}
          modelId={model_id}
          editable={editable ?? user.hasChangePermission(model_type)}
        />
      ) : (
        <Skeleton />
      ),
    supportsDirty: true
  };
}
