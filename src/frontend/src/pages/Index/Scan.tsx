import { Trans } from '@lingui/macro';
import { Col, Container, Grid, Group, Space, Text } from '@mantine/core';

import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';

export default function Scan() {
  return (
    <>
      <Group>
        <StylishText>
          <Trans>Scan Page</Trans>
        </StylishText>
      </Group>
      <Space h={'md'} />
      <Grid maw={'100%'}>
        <Col span={4} bg={'grape'}>
          Interactive Scanning window
          <PlaceholderPill />
        </Col>
        <Col span={8} bg={'indigo'}>
          Entries
          <PlaceholderPill />
        </Col>
      </Grid>
    </>
  );
}
