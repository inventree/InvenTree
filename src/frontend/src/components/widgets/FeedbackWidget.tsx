import { Trans } from '@lingui/macro';
import { Button, Stack, Title } from '@mantine/core';
import { IconExternalLink } from '@tabler/icons-react';

export default function FeedbackWidget() {
  return (
    <Stack
      sx={(theme) => ({
        backgroundColor:
          theme.colorScheme === 'dark'
            ? theme.colors.gray[9]
            : theme.colors.gray[1],
        borderRadius: theme.radius.md
      })}
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
        leftIcon={<IconExternalLink size="0.9rem" />}
      >
        <Trans>Provide Feedback</Trans>
      </Button>
    </Stack>
  );
}
