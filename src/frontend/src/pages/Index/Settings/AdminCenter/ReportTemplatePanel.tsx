import { t } from '@lingui/macro';

import { YesNoButton } from '../../../../components/buttons/YesNoButton';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { ModelType } from '../../../../enums/ModelType';
import { TemplateTable } from '../../../../tables/settings/TemplateTable';

export default function ReportTemplateTable() {
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
          }
        }
      }}
    />
  );
}
