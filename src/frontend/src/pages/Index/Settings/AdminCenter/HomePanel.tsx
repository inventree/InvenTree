import { Trans } from '@lingui/macro';
import { Divider, Stack, Title } from '@mantine/core';

export default function HomePanel() {
  return (
    <Stack gap="xs">
      <Title order={5}>
        <Trans>Home Status Panel</Trans>
      </Title>

      <Divider />
    </Stack>
  );
}
