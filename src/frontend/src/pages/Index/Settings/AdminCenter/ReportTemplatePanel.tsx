import { YesNoButton } from '@lib/components/YesNoButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { t } from '@lingui/core/macro';
import { lazy } from 'react';

const TemplateTable = lazy(() =>
  import('../../../../tables/settings/TemplateTable').then((module) => ({
    default: module.TemplateTable
  }))
);

function ReportTemplateTable() {
  return (
    <TemplateTable
      templateProps={{
        modelType: ModelType.reporttemplate,
        templateEndpoint: ApiEndpoints.report_list,
        printingEndpoint: ApiEndpoints.report_print,
        additionalFilters: [
          {
            name: 'landscape',
            label: t`Landscape`,
            type: 'boolean'
          },
          {
            name: 'merge',
            label: t`Merge`,
            type: 'boolean'
          },
          {
            name: 'attach_to_model',
            label: t`Attach to Model`,
            type: 'boolean'
          }
        ],
        additionalFormFields: {
          page_size: {
            label: t`Page Size`
          },
          landscape: {
            label: t`Landscape`,
            filter: 'landscape',
            modelRenderer: (instance: any) => (
              <YesNoButton value={instance.landscape} />
            )
          },
          merge: {
            label: t`Merge`,
            filter: 'merge',
            modelRenderer: (instance: any) => (
              <YesNoButton value={instance.merge} />
            )
          },
          attach_to_model: {
            label: t`Attach to Model`,
            filter: 'attach_to_model',
            modelRenderer: (instance: any) => (
              <YesNoButton value={instance.attach_to_model} />
            )
          }
        }
      }}
    />
  );
}

export default function ReportTemplatePanel() {
  return <ReportTemplateTable />;
}
