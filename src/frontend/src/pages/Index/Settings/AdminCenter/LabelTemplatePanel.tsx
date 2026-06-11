import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { TemplateTable } from '../../../../tables/settings/TemplateTable';

function LabelTemplateTable() {
  return (
    <TemplateTable
      templateProps={{
        modelType: ModelType.labeltemplate,
        templateEndpoint: ApiEndpoints.label_list,
        printingEndpoint: ApiEndpoints.label_print,
        additionalFormFields: {
          width: {
            sortable: true
          },
          height: {
            sortable: true
          }
        }
      }}
    />
  );
}

export default function LabelTemplatePanel() {
  return <LabelTemplateTable />;
}
