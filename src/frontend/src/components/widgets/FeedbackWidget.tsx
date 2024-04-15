import { Trans } from '@lingui/macro';
import { Button, Stack, Title } from '@mantine/core';
import { useColorScheme } from '@mantine/hooks';
import { IconExternalLink } from '@tabler/icons-react';

import { vars } from '../../theme';

export default function FeedbackWidget() {
  const [preferredColorScheme] = useColorScheme();
  return (
    <Stack
      style={{
        backgroundColor:
          preferredColorScheme === 'dark'
            ? vars.colors.gray[9]
            : vars.colors.gray[1],
        borderRadius: vars.radius.md
      }}
      p={15}
    >
      <Title order={5}>
        <Trans>Something is new: Platform UI</Trans>
      </Title>
      <Trans>
        We are building a new UI with a modern stack. What you currently see is
        not fixed and will be redesigned but demonstrates the UI/UX
        possibilities we will have going forward.
      </Trans>
      <Button
        component="a"
        href="https://github.com/inventree/InvenTree/discussions/5328"
        variant="outline"
        leftSection={<IconExternalLink size="0.9rem" />}
      >
        <Trans>Provide Feedback</Trans>
      </Button>
    </Stack>
  );
}
