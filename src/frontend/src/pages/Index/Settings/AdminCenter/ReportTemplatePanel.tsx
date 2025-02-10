import { t } from '@lingui/macro';

import { Accordion } from '@mantine/core';
import { YesNoButton } from '../../../../components/buttons/YesNoButton';
import { StylishText } from '../../../../components/items/StylishText';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { ModelType } from '../../../../enums/ModelType';
import {
  TemplateOutputTable,
  TemplateTable
} from '../../../../tables/settings/TemplateTable';

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
  return (
    <Accordion defaultValue={['templates']} multiple>
      <Accordion.Item value='templates'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Report Templates`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <ReportTemplateTable />
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value='outputs'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Generated Reports`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <TemplateOutputTable endpoint={ApiEndpoints.report_output} />
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
