import { t } from '@lingui/macro';
import { Accordion } from '@mantine/core';

import { StylishText } from '../../../../components/items/StylishText';
import PartParameterTemplateTable from '../../../../tables/part/PartParameterTemplateTable';
import SelectionListTable from '../../../../tables/part/SelectionListTable';

export default function PartParameterPanel() {
  return (
    <>
      <PartParameterTemplateTable />

      <Accordion>
        <Accordion.Item value='selectionlist' key='selectionlist'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Selection Lists`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <SelectionListTable />
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </>
  );
}
