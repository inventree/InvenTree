import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { TemplateTable } from '../../../../tables/settings/TemplateTable';

export default function ReportTemplateTable() {
  return (
    <TemplateTable
      templateProps={{
        templateEndpoint: ApiEndpoints.report_list,
        printingEndpoint: ApiEndpoints.report_print,
        templateType: 'report',
        additionalFormFields: {
          page_size: {},
          landscape: {}
        }
      }}
    />
  );
}
