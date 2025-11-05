import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Divider, Group, Paper, Stack, Text, TextInput } from '@mantine/core';
import { QRCode } from '../../../../components/barcodes/QRCode';
import { CopyButton } from '../../../../components/buttons/CopyButton';

export function QrRegistrationForm({
  url,
  secret,
  value,
  error,
  setValue
}: Readonly<{
  url: string;
  secret: string;
  value: string;
  error?: string;
  setValue: (value: string) => void;
}>) {
  return (
    <Stack gap='xs'>
      <Divider />
      <QRCode data={url} />
      <Paper withBorder p='sm' aria-label='otp-secret-container'>
        <Stack gap='xs'>
          <Text>
            <Trans>Secret</Trans>
          </Text>
          <Group justify='space-between'>
            <Text size='sm' aria-label='otp-secret'>
              {secret}
            </Text>
            <CopyButton value={secret} />
          </Group>
        </Stack>
      </Paper>
      <TextInput
        required
        aria-label={'text-input-otp-code'}
        label={t`One-Time Password`}
        description={t`Enter the TOTP code to ensure it registered correctly`}
        value={value}
        onChange={(event) => setValue(event.currentTarget.value)}
        error={error}
      />
      <Divider />
    </Stack>
  );
}
