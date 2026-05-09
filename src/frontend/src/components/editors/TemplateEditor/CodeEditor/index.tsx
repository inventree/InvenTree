import { t } from '@lingui/core/macro';
import { IconCode } from '@tabler/icons-react';

import { lazy } from 'react';
import type { Editor } from '../TemplateEditor';

const CodeEditorComponent = lazy(() =>
  import('./CodeEditor').then((module) => ({
    default: module.CodeEditorComponent
  }))
);

export const CodeEditor: Editor = {
  key: 'code',
  name: t`Code`,
  icon: <IconCode size={18} />,
  component: CodeEditorComponent
};
