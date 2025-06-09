import { Trans } from '@lingui/react/macro';
import { forwardRef, useImperativeHandle, useState } from 'react';

import { ApiEndpoints, apiUrl } from '@lib/index';
import { api } from '../../../../App';
import type { PreviewAreaComponent } from '../TemplateEditor';

export const PdfPreviewComponent: PreviewAreaComponent = forwardRef(
  (props, ref) => {
    const [pdfUrl, setPdfUrl] = useState('');

    useImperativeHandle(ref, () => ({
      updatePreview: async (
        code,
        previewItem,
        saveTemplate,
        { templateUrl, printingUrl, template }
      ) => {
        if (saveTemplate) {
          const formData = new FormData();

          const filename =
            template.template?.split('/').pop() ?? 'template.html';

          formData.append('template', new File([code], filename));

          const res = await api.patch(templateUrl, formData);
          if (res.status !== 200) {
            throw new Error(res.data);
          }
        }

        let preview = await api.post(
          printingUrl,
          {
            items: [previewItem],
            template: template.pk
          },
          {
            responseType: 'json',
            timeout: 30000,
            validateStatus: () => true
          }
        );

        if (preview.status !== 200 && preview.status !== 201) {
          if (preview.data?.non_field_errors) {
            throw new Error(preview.data?.non_field_errors.join(', '));
          }

          throw new Error(preview.data);
        }

        let outputUrl = preview?.data?.output;
        if (preview.data && !preview.data.complete) {
          outputUrl = await new Promise((res, rej) => {
            let cnt = 0;
            const interval = setInterval(() => {
              api
                .get(apiUrl(ApiEndpoints.data_output, preview.data.pk))
                .then((response) => {
                  if (response.data.error) {
                    clearInterval(interval);
                    rej(response.data.error);
                  }

                  if (response.data.complete) {
                    clearInterval(interval);
                    res(response.data.output);
                  }

                  // timeout after 1 minute
                  if (cnt > 2 * 60) {
                    clearInterval(interval);
                    rej('Timeout');
                  }
                  cnt++;
                });
            }, 500);
          });
        }

        if (outputUrl) {
          preview = await api.get(outputUrl, {
            responseType: 'blob'
          });
        }

        const pdf = new Blob([preview.data], {
          type: preview.headers['content-type']
        });

        const srcUrl = URL.createObjectURL(pdf);

        setPdfUrl(`${srcUrl}#view=fitH`);
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
        {pdfUrl && (
          <iframe src={pdfUrl} width='100%' height='100%' title='PDF Preview' />
        )}
      </>
    );
  }
);
