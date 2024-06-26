import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { TemplateTable } from '../../../../tables/settings/TemplateTable';

export default function LabelTemplatePanel() {
  return (
    <TemplateTable
      templateProps={{
        templateEndpoint: ApiEndpoints.label_list,
        printingEndpoint: ApiEndpoints.label_print,
        additionalFormFields: {
          width: {},
          height: {}
        }
      }}
    />
  );
}
