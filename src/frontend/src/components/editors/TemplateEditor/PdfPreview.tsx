import { Trans } from '@lingui/macro';
import { forwardRef, useImperativeHandle, useState } from 'react';

import { api } from '../../../App';
import { PreviewAreaComponent } from './TemplateEditor';

export const PdfPreview: PreviewAreaComponent = forwardRef((props, ref) => {
  const [pdfUrl, setPdfUrl] = useState('');

  useImperativeHandle(ref, () => ({
    updatePreview: async (
      code,
      previewItem,
      saveTemplate,
      { uploadKey, uploadUrl, preview: { itemKey }, templateType }
    ) => {
      if (saveTemplate) {
        const formData = new FormData();
        formData.append(uploadKey, new File([code], 'template.html'));

        const res = await api.patch(uploadUrl, formData);
        if (res.status !== 200) {
          throw new Error(res.data);
        }
      }

      // ---- TODO: Fix this when implementing the new API ----
      let preview = await api.get(
        uploadUrl + `print/?plugin=inventreelabel&${itemKey}=${previewItem}`,
        {
          responseType: templateType === 'label' ? 'json' : 'blob',
          timeout: 30000,
          validateStatus: () => true
        }
      );

      if (preview.status !== 200) {
        if (preview.data?.non_field_errors) {
          throw new Error(preview.data?.non_field_errors.join(', '));
        }

        throw new Error(preview.data);
      }

      if (templateType === 'label') {
        preview = await api.get(preview.data.file, {
          responseType: 'blob'
        });
      }
      // ----
      let pdf = new Blob([preview.data], {
        type: preview.headers['content-type']
      });
      let srcUrl = URL.createObjectURL(pdf);

      setPdfUrl(srcUrl + '#view=fitH');
    }
  }));

  return (
    <>
      {!pdfUrl && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100%'
          }}
        >
          <Trans>Preview not available, click "Reload Preview".</Trans>
        </div>
      )}
      {pdfUrl && <iframe src={pdfUrl} width="100%" height="100%" />}
    </>
  );
});
