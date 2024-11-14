import { t } from '@lingui/macro';
import { Accordion } from '@mantine/core';

import { StylishText } from '../../components/items/StylishText';
import { ManufacturerPartTable } from '../../tables/purchasing/ManufacturerPartTable';
import { SupplierPartTable } from '../../tables/purchasing/SupplierPartTable';

export default function PartSupplierDetail({
  partId
}: Readonly<{ partId: number }>) {
  return (
    <Accordion multiple defaultValue={['part-suppliers', 'part-manufacturers']}>
      <Accordion.Item value='part-suppliers'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Suppliers`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <SupplierPartTable params={{ part: partId }} />
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value='part-manufacturers'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Manufacturers`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <ManufacturerPartTable params={{ part: partId }} />
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
