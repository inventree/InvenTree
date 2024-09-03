import { t } from '@lingui/macro';
import { ActionIcon, Box, Button, Divider, TextInput } from '@mantine/core';
import { IconQrcode } from '@tabler/icons-react';
import React, { useState } from 'react';

import { InputImageBarcode } from '../../pages/Index/Scan';

type BarcodeInputProps = {
  onScan: (decodedText: string) => void;
  value?: string;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onAction?: () => void;
  placeholder?: string;
  label?: string;
  actionText?: string;
};

export function BarcodeInput({
  onScan,
  value,
  onChange,
  onAction,
  placeholder = t`Scan barcode data here using barcode scanner`,
  label = t`Barcode`,
  actionText = t`Scan`
}: Readonly<BarcodeInputProps>) {
  const [isScanning, setIsScanning] = useState(false);

  return (
    <Box>
      {isScanning && (
        <>
          <InputImageBarcode action={onScan} />
          <Divider mt={'sm'} />
        </>
      )}
      <TextInput
        label={label}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        leftSection={
          <ActionIcon
            variant={isScanning ? 'filled' : 'subtle'}
            onClick={() => setIsScanning(!isScanning)}
          >
            <IconQrcode />
          </ActionIcon>
        }
        w="100%"
      />
      {onAction ? (
        <Button color="green" onClick={onAction} mt="lg" fullWidth>
          {actionText}
        </Button>
      ) : null}
    </Box>
  );
}
