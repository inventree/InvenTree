import { t } from '@lingui/core/macro';
import { Button, FocusTrap, Stack, TextInput } from '@mantine/core';
import { IconQrcode } from '@tabler/icons-react';
import { useCallback, useState } from 'react';
import type { BarcodeInputProps } from './BarcodeInput';

// Control keys commonly used for ASCII control codes by barcode scanners
// emulating keyboard input.
// See for example: https://docs.zebra.com/us/en/scanners/general/sm72-ig/ascii-character-sets.html
const BarcodeControlKeys: Record<string, string> = {
  KeyD: String.fromCharCode(4), // End of transmission
  BracketRight: String.fromCharCode(29), // Group separator
  Digit6: String.fromCharCode(30) // Record separator
} as const;

export default function BarcodeKeyboardInput({
  onScan,
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
              let key = event.key;

              if (event.ctrlKey) {
                if (event.code in BarcodeControlKeys) {
                  // Prevent most of the keyboard shortcuts.
                  // Not all of them will be blocked, browser don't allow this:
                  // https://stackoverflow.com/questions/59952382/using-preventdefault-to-override-opening-new-tab
                  event.preventDefault();
                  key = BarcodeControlKeys[event.code];
                  setText((prev) => prev + key);
                }
              }

              if (
                key === 'Enter' ||
                key === String.fromCharCode(4) // End of transmission
              ) {
                onTextScan(text);
              }
            }}
            placeholder={t`Enter barcode data`}
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
