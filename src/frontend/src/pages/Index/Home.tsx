import { Trans } from '@lingui/macro';
import { Anchor, Group, Stack, Text, Title } from '@mantine/core';

import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
import { useApiState } from '../../states/ApiState';
import { CardsCarousel } from './CardsCarousel';
import ToolboxLayout from './toolboxwidget';

export default function Home() {
  const [username] = useApiState((state) => [state.user?.name]);
  return (
    <>
      <Group>
        <StylishText>
          <Trans>Home</Trans>
        </StylishText>
        <PlaceholderPill />
      </Group>
      <Title order={2}>
        <Trans>Welcome to your Dashboard{username && `, ${username}`}</Trans>
      </Title>
      <Stack style={{ border: `1px solid`, borderRadius: 5 }} px={5}>
        <Title order={5}>
          <Trans>Something is new: Platform UI</Trans>
        </Title>
        <Text>
          <Trans>Small welcome text with info about the new UI</Trans>
        </Text>
        <Anchor
          href="https://github.com/inventree/InvenTree/discussions/5328"
          target="_blank"
        >
          <Trans>Provide feedback</Trans>
        </Anchor>
      </Stack>

      <Title order={5}>
        <Trans>Getting started</Trans>
      </Title>
      <CardsCarousel />

      <Title order={5}>
        <Trans>Widgets</Trans>
      </Title>
      <ToolboxLayout />
    </>
  );
}
