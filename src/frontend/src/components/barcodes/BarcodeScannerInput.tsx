import { t } from '@lingui/macro';
import {
  Box,
  Center,
  Container,
  FocusTrap,
  Group,
  Loader,
  Stack,
  Text,
  TextInput,
  VisuallyHidden
} from '@mantine/core';
import { useTimeout } from '@mantine/hooks';
import { IconScan } from '@tabler/icons-react';
import { useCallback, useEffect, useState } from 'react';
import type { BarcodeInputProps } from './BarcodeInput';

export default function BarcodeScannerInput({
  onScan
}: Readonly<BarcodeInputProps>) {
  const [barcodeData, setBarcodeData] = useState<string>('');

  const { start, clear } = useTimeout(() => setBarcodeData(''), 500);

  const onKeyPress = useCallback(
    (event: any) => {
      if (event.key === 'Enter') {
        onScan(barcodeData);
        setBarcodeData('');
        clear();
      } else {
        setBarcodeData((barcode) => barcode + event.key);
        clear();
        start();
      }
    },
    [barcodeData, onScan]
  );

  useEffect(() => {
    // Add event listener
    window.addEventListener('keypress', onKeyPress);
    // Remove event listener
    return () => {
      window.removeEventListener('keypress', onKeyPress);
    };
  }, [onKeyPress]);

  return (
    <>
      <Box>
        <Container>
          <Center>
            <FocusTrap active={true}>
              <Stack gap='xs'>
                {/* Hidden input, required for FocusTrap to work */}
                <VisuallyHidden>
                  <TextInput hidden />
                </VisuallyHidden>
                <Group justify='space-apart'>
                  <IconScan size={64} />
                  <Loader />
                </Group>
              </Stack>
            </FocusTrap>
          </Center>
          <Center>
            {barcodeData ? (
              <Text>{barcodeData}</Text>
            ) : (
              <Text>{t`Waiting for scanner input`}</Text>
            )}
          </Center>
        </Container>
      </Box>
    </>
  );
}
