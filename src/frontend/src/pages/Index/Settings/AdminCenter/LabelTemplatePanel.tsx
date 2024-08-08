import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { ModelType } from '../../../../enums/ModelType';
import { TemplateTable } from '../../../../tables/settings/TemplateTable';

export default function LabelTemplatePanel() {
  return (
    <TemplateTable
      templateProps={{
        modelType: ModelType.labeltemplate,
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
