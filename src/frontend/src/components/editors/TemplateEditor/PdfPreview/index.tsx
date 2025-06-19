import { t } from '@lingui/core/macro';
import { IconFileTypePdf } from '@tabler/icons-react';

import type { PreviewArea } from '../TemplateEditor';
import { PdfPreviewComponent } from './PdfPreview';

export const PdfPreview: PreviewArea = {
  key: 'pdf-preview',
  name: t`PDF Preview`,
  icon: <IconFileTypePdf size={18} />,
  component: PdfPreviewComponent
};
