import { t } from '@lingui/macro';
import { IconUpload } from '@tabler/icons-react';

import { ActionButton } from '../components/buttons/ActionButton';

export function UploadAction({}) {
  return <ActionButton icon={<IconUpload />} tooltip={t`Upload Data`} />;
}
