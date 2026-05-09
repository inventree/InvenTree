import { t } from '@lingui/core/macro';
import { IconCode } from '@tabler/icons-react';

import type { Editor } from '../TemplateEditor';
import { CodeEditorComponent } from './CodeEditor';

export const CodeEditor: Editor = {
  key: 'code',
  name: t`Code`,
  icon: <IconCode size={18} />,
  component: CodeEditorComponent
};
