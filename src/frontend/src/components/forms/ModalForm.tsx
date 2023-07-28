import { Divider, LoadingOverlay, Stack, Text } from '@mantine/core';

import { ApiFormProps } from './ApiForm';

export function ModalFormContent(props: ApiFormProps) {
  return (
    <Stack>
      <Divider />
      <Stack spacing="sm">
        <LoadingOverlay visible={false} />
      </Stack>
      <Text>Hello</Text>
      <Text>There</Text>
    </Stack>
  );
}
