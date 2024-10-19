import { t } from '@lingui/macro';
import { Alert, Text } from '@mantine/core';

export function ErrorItem({
  id,
  error
}: Readonly<{ id: string; error?: any }>) {
  const error_message = error?.message || error?.toString() || t`Unknown error`;

  return (
    <>
      <Alert color='red' title={t`An error occurred`}>
        <Text>{error_message}</Text>
      </Alert>
    </>
  );
}
