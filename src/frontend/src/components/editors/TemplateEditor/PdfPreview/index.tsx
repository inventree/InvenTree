import { t } from '@lingui/macro';
import { IconFileTypePdf } from '@tabler/icons-react';

import { PreviewArea } from '../TemplateEditor';
import { PdfPreviewComponent } from './PdfPreview';

export const PdfPreview: PreviewArea = {
  key: 'pdf-preview',
  name: t`PDF Preview`,
  icon: IconFileTypePdf,
  component: PdfPreviewComponent
};
