import { Trans } from '@lingui/macro';
import { forwardRef, useImperativeHandle, useState } from 'react';

import { PreviewAreaComponent } from '.';
import { api } from '../../../App';

export const PreviewArea: PreviewAreaComponent = forwardRef((props, ref) => {
  const [pdfUrl, setPdfUrl] = useState('');

  useImperativeHandle(ref, () => ({
    updatePreview: async (
      code,
      previewItem,
      { uploadKey, uploadUrl, preview: { itemKey }, templateType }
    ) => {
      const formData = new FormData();
      formData.append(uploadKey, new File([code], 'template.html'));

      const res = await api.patch(uploadUrl, formData);
      if (res.status !== 200) {
        return console.log('An error occurred while uploading the template');
      }

      // ---- Fix this when implementing the new API ----
      let preview = await api.get(
        uploadUrl + `print/?plugin=inventreelabel&${itemKey}=${previewItem}`,
        { responseType: templateType === 'label' ? 'json' : 'blob' }
      );

      if (preview.status !== 200) {
        return console.log(
          'An error occurred while fetching the preview',
          preview.data
        );
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

      setPdfUrl(srcUrl + '#view=fitv');
    }
  }));

  if (!pdfUrl)
    return (
      <div>
        <Trans>Preview not available, click "Reload Preview".</Trans>
      </div>
    );

  return (
    <div style={{ height: '60vh' }}>
      <iframe src={pdfUrl} width="100%" height="100%" />
    </div>
  );
});
