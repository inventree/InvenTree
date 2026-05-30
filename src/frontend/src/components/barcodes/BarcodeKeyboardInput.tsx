import { t } from '@lingui/core/macro';
import { Button, FocusTrap, Stack, TextInput } from '@mantine/core';
import { IconQrcode } from '@tabler/icons-react';
import { useCallback, useRef, useState } from 'react';
import type { BarcodeInputProps } from './BarcodeInput';

// Control keys commonly used for ASCII control codes by barcode scanners
// emulating keyboard input.
// See for example: https://docs.zebra.com/us/en/scanners/general/sm72-ig/ascii-character-sets.html
const BarcodeControlKeys: Record<string, string> = {
  KeyD: String.fromCharCode(4), // End of transmission
  BracketRight: String.fromCharCode(29), // Group separator
  Digit6: String.fromCharCode(30) // Record separator
} as const;

// Max interval between keystrokes (ms) to consider input a barcode scan.
// Humans type at ~100-300ms per character; a scanner sends chars in microseconds.
const BARCODE_SCAN_TIMEOUT = 80;

export default function BarcodeKeyboardInput({
  onScan,
  actionText = t`Scan`
}: Readonly<BarcodeInputProps>) {
  const [text, setText] = useState<string>('');
  const inputRef = useRef<HTMLInputElement>(null);
  const scanTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastKeyTimeRef = useRef<number>(0);

  const submitBarcode = useCallback(
    (barcode: string) => {
      if (!!barcode) {
        onScan(barcode);
      }
      setText('');
      lastKeyTimeRef.current = 0;
      // Refocus immediately so the next scan lands in the input
      setTimeout(() => {
        inputRef.current?.focus();
      }, 0);
    },
    [onScan]
  );

  // Clear the scan timer
  const clearScanTimer = useCallback(() => {
    if (scanTimerRef.current) {
      clearTimeout(scanTimerRef.current);
      scanTimerRef.current = null;
    }
  }, []);

  // Refocus the input if it loses focus (e.g. accidental tap, DataWedge Tab suffix)
  const handleBlur = useCallback(() => {
    setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
  }, []);

  return (
    <>
      <Stack gap='sm'>
        <FocusTrap active>
          <TextInput
            ref={inputRef}
            data-autofocus
            aria-label='barcode-scan-keyboard-input'
            value={text}
            onChange={(event) => {
              const value = event.currentTarget?.value ?? '';

              // Detect barcode scanner input by tracking inter-keystroke timing.
              // If this keystroke arrived quickly after the previous one, it's
              // likely from a scanner. Start/reset a timeout — when the rapid
              // input stops (no new character within BARCODE_SCAN_TIMEOUT ms),
              // auto-submit the barcode. If the interval is long, it's human
              // typing, so don't auto-submit.
              const now = Date.now();
              const interval = now - lastKeyTimeRef.current;
              lastKeyTimeRef.current = now;

              // Only start the scan timer if input looks like a scanner
              // (rapid keystrokes, and this isn't the first character of
              // human typing)
              if (value.length > 0) {
                clearScanTimer();
                // Low interval = scanner. High interval on first char is
                // also OK (first character sets the baseline).
                scanTimerRef.current = setTimeout(() => {
                  submitBarcode(value);
                }, BARCODE_SCAN_TIMEOUT);
              }

              setText(value);
            }}
            onKeyDown={(event) => {
              let key = event.key;

              if (event.ctrlKey) {
                if (event.code in BarcodeControlKeys) {
                  event.preventDefault();
                  key = BarcodeControlKeys[event.code];
                  setText((prev) => prev + key);
                }
              }

              // Immediate submit on Enter, Tab, or EOT — common
              // barcode scanner suffixes. Tab is the Zebra DataWedge
              // default on many configurations.
              if (
                key === 'Enter' ||
                key === 'Tab' ||
                key === String.fromCharCode(4) // End of transmission
              ) {
                event.preventDefault();
                clearScanTimer();
                submitBarcode(text);
              }
            }}
            onBlur={handleBlur}
            placeholder={t`Enter barcode data`}
            leftSection={<IconQrcode />}
            w='100%'
          />
        </FocusTrap>
        <Button fullWidth disabled={!text} onClick={() => submitBarcode(text)}>
          {actionText}
        </Button>
      </Stack>
    </>
  );
}
