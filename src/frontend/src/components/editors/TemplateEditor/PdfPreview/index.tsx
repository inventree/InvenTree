import { t } from '@lingui/core/macro';
import { IconFileTypePdf } from '@tabler/icons-react';

import { lazy } from 'react';
import type { PreviewArea } from '../TemplateEditor';

const PdfPreviewComponent = lazy(() =>
  import('./PdfPreview').then((module) => ({
    default: module.PdfPreviewComponent
  }))
);

export const PdfPreview: PreviewArea = {
  key: 'pdf-preview',
  name: t`PDF Preview`,
  icon: <IconFileTypePdf size={18} />,
  component: PdfPreviewComponent
};
