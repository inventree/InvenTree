import { Trans } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { useParams } from 'react-router-dom';

import { StylishText } from '../../components/items/StylishText';

export default function PurchaseOrderDetail() {
  const { pk } = useParams();

  return (
    <>
      <Group>
        <StylishText>
          <Trans>Purchase Order</Trans>
        </StylishText>
      </Group>
      <Text>{pk}</Text>
    </>
  );
}
