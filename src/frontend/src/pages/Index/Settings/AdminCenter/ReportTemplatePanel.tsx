import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { t } from '@lingui/core/macro';
import { YesNoButton } from '../../../../components/buttons/YesNoButton';
import { TemplateTable } from '../../../../tables/settings/TemplateTable';

function ReportTemplateTable() {
  return (
    <TemplateTable
      templateProps={{
        modelType: ModelType.reporttemplate,
        templateEndpoint: ApiEndpoints.report_list,
        printingEndpoint: ApiEndpoints.report_print,
        additionalFormFields: {
          page_size: {
            label: t`Page Size`
          },
          landscape: {
            label: t`Landscape`,
            modelRenderer: (instance: any) => (
              <YesNoButton value={instance.landscape} />
            )
          },
          attach_to_model: {
            label: t`Attach to Model`,
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
