import { Trans } from '@lingui/macro';
import { Container, Grid, Group, Text, Title } from '@mantine/core';
import { useParams } from 'react-router-dom';

import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';

export default function PurchaseOrderDetail() {
  const { pk } = useParams();

  return (
    <>
      <Group>
        <StylishText>
          <Trans>Purchase Order</Trans>
        </StylishText>
        <PlaceholderPill />
      </Group>
      <Grid grow>
        <Grid.Col span={8}>
          {' '}
          <Title>
            <Trans>Details for {pk} here</Trans>
          </Title>
          <PlaceholderPill />
        </Grid.Col>
        <Grid.Col span={2}>
          <Text>
            <Trans>Sidebar</Trans>
          </Text>
        </Grid.Col>
      </Grid>
    </>
  );
}
