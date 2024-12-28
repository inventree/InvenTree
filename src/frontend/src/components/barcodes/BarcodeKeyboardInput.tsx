import { t } from '@lingui/macro';
import { Button, FocusTrap, Stack, TextInput } from '@mantine/core';
import { IconQrcode } from '@tabler/icons-react';
import { useCallback, useState } from 'react';
import type { BarcodeInputProps } from './BarcodeInput';

export default function BarcodeKeyboardInput({
  onScan,
  placeholder = t`Input barcode data using keyboard`,
  actionText = t`Scan`
}: Readonly<BarcodeInputProps>) {
  const [text, setText] = useState<string>('');

  const onTextScan = useCallback(
    (barcode: string) => {
      if (!!barcode) {
        onScan(barcode);
      }
      setText('');
    },
    [onScan]
  );

  return (
    <>
      <Stack gap='sm'>
        <FocusTrap active>
          <TextInput
            data-autofocus
            aria-label='barcode-scan-keyboard-input'
            value={text}
            onChange={(event) => {
              setText(event.currentTarget?.value);
            }}
            onKeyDown={(event) => {
              if (event.code === 'Enter') {
                onTextScan(text);
              }
            }}
            placeholder={placeholder}
            leftSection={<IconQrcode />}
            w='100%'
          />
        </FocusTrap>
        <Button fullWidth disabled={!text} onClick={() => onTextScan(text)}>
          {actionText}
        </Button>
      </Stack>
    </>
  );
}
