import { Trans, t } from '@lingui/macro';
import { forwardRef, useImperativeHandle, useState } from 'react';

import { api } from '../../../../App';
import { PreviewAreaComponent } from '../TemplateEditor';

export const PdfPreviewComponent: PreviewAreaComponent = forwardRef(
  (props, ref) => {
    const [pdfUrl, setPdfUrl] = useState('');

    useImperativeHandle(ref, () => ({
      updatePreview: async (
        code,
        previewItem,
        saveTemplate,
        { url, template, templateType }
      ) => {
        if (saveTemplate) {
          const formData = new FormData();
          formData.append('template', new File([code], 'template.html'));

          const res = await api.patch(url, formData);
          if (res.status !== 200) {
            throw new Error(res.data);
          }
        }

        // ---- TODO: Fix this when implementing the new API ----
        let preview = await api.get(
          url + `print/?plugin=inventreelabel&items=${previewItem}`,
          {
            responseType: templateType === 'label' ? 'json' : 'blob',
            timeout: 30000,
            validateStatus: () => true
          }
        );

        if (preview.status !== 200 && preview.status !== 201) {
          if (templateType === 'report') {
            let data;
            try {
              data = JSON.parse(await preview.data.text());
            } catch (err) {
              throw new Error(t`Failed to parse error response from server.`);
            }

            throw new Error(data.detail?.join(', '));
          } else if (preview.data?.non_field_errors) {
            throw new Error(preview.data?.non_field_errors.join(', '));
          }

          throw new Error(preview.data);
        }

        console.log('Response:', templateType, preview.data);

        if (templateType === 'label') {
          preview = await api.get(preview.data.output, {
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
              height: '100%',
              width: '100%'
            }}
          >
            <Trans>Preview not available, click "Reload Preview".</Trans>
          </div>
        )}
        {pdfUrl && <iframe src={pdfUrl} width="100%" height="100%" />}
      </>
    );
  }
);
