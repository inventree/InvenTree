import { Trans } from '@lingui/macro';
import { Button, Stack, Text } from '@mantine/core';
import { ContextModalProps } from '@mantine/modals';

export function ServerInfoModal({
  context,
  id
}: ContextModalProps<{ modalBody: string }>) {
  return (
    <Stack>
      <Text>Testdata</Text>
      <Button
        fullWidth
        mt="md"
        color="red"
        onClick={() => {
          context.closeModal(id);
        }}
      >
        <Trans>Close modal</Trans>
      </Button>
    </Stack>
  );
}
