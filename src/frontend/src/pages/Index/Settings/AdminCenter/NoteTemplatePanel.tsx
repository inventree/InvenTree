import { t } from '@lingui/core/macro';
import { Alert, Stack } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';
import NotesEditor from '../../../../components/editors/NotesEditor';

export default function NoteTemplatePanel() {
  return (
    <Stack gap='xs'>
      <Alert color='blue' icon={<IconInfoCircle />} title={t`Note Templates`}>
        {t`Note templates can be used to create pre-defined notes which can be easily added to any model instance.`}
      </Alert>
      <NotesEditor templateMode />
    </Stack>
  );
}
