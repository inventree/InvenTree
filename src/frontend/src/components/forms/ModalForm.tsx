import { LoadingOverlay, Stack, Text } from '@mantine/core';

export function ModalFormContent() {
  return (
    <>
      <Stack spacing="sm">
        <LoadingOverlay visible={false} />
        <Text>hello</Text>
        <Text>world</Text>
      </Stack>
    </>
  );
}
