import { t } from '@lingui/core/macro';
import { Skeleton } from '@mantine/core';
import { IconNotes } from '@tabler/icons-react';

import type { ModelType } from '@lib/enums/ModelType';
import type { PanelType } from '@lib/types/Panel';
import NotesEditor from '../editors/NotesEditor';

// const NotesEditor = lazy(() => import('../editors/NotesEditor'));

export default function NotesPanel({
  model_type,
  model_id,
  editable,
  note_count
}: {
  model_type: ModelType;
  model_id: number | undefined;
  editable?: boolean;
  note_count?: number;
}): PanelType {
  return {
    name: 'notes',
    label: t`Notes`,
    icon: <IconNotes />,
    hotkey: 'mod+Shift+N',
    notification_dot: note_count ? 'info' : null,
    content:
      model_type && model_id ? (
        <NotesEditor modelType={model_type} modelId={model_id} />
      ) : (
        <Skeleton />
      ),
    supportsDirty: true
  };
}
