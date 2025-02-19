import { Trans, t } from '@lingui/macro';
import { Divider, Text, TextInput } from '@mantine/core';
import { QRCode } from '../../../../components/barcodes/QRCode';

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
    <>
      <Divider />
      <QRCode data={url} />
      <Text>
        <Trans>Secret</Trans>
        <br />
        {secret}
      </Text>
      <TextInput
        required
        label={t`One-Time Password`}
        description={t`Enter the TOTP code to ensure it registered correctly`}
        value={value}
        onChange={(event) => setValue(event.currentTarget.value)}
        error={error}
      />
    </>
  );
}
