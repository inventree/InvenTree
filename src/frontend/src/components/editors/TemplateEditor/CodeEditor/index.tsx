import { t } from '@lingui/macro';
import { IconCode } from '@tabler/icons-react';

import { Editor } from '../TemplateEditor';
import { CodeEditorComponent } from './CodeEditor';

export const CodeEditor: Editor = {
  key: 'code',
  name: t`Code`,
  icon: IconCode,
  component: CodeEditorComponent
};
