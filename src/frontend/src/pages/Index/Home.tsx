import { Trans } from '@lingui/macro';
import { Anchor, Group, Stack, Text, Title } from '@mantine/core';

import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
import { useApiState } from '../../states/ApiState';
import { LocalStorageLayout } from './toolboxwidget';

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
      <Title order={3}>
        <Trans>Welcome to your Dashboard{username && `, ${username}`}</Trans>
      </Title>

      <LocalStorageLayout />
    </>
  );
}
