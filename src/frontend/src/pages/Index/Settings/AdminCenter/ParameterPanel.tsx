import { t } from '@lingui/core/macro';
import { Accordion } from '@mantine/core';

import { StylishText } from '../../../../components/items/StylishText';
import ParameterTemplateTable from '../../../../tables/general/ParameterTemplateTable';
import SelectionListTable from '../../../../tables/part/SelectionListTable';

export default function PartParameterPanel() {
  return (
    <Accordion multiple defaultValue={['parameter-templates']}>
      <Accordion.Item value='parameter-templates' key='parameter-templates'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Parameter Templates`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <ParameterTemplateTable />
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value='selection-lists' key='selection-lists'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Selection Lists`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <SelectionListTable />
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
