import { t } from '@lingui/macro';
import { Accordion } from '@mantine/core';
import { StylishText } from '../../../../components/items/StylishText';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { ModelType } from '../../../../enums/ModelType';
import {
  TemplateOutputTable,
  TemplateTable
} from '../../../../tables/settings/TemplateTable';

function LabelTemplateTable() {
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

export default function LabelTemplatePanel() {
  return (
    <Accordion defaultValue={['templates']} multiple>
      <Accordion.Item value='templates'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Label Templates`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <LabelTemplateTable />
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value='outputs'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Generated Labels`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <TemplateOutputTable
            endpoint={ApiEndpoints.label_output}
            withPlugins
          />
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
