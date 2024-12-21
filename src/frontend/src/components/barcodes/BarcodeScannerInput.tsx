import { t } from '@lingui/macro';
import {
  Box,
  Center,
  Container,
  FocusTrap,
  Group,
  Loader,
  Stack,
  Text
} from '@mantine/core';
import { IconScan } from '@tabler/icons-react';
import { useCallback, useEffect, useState } from 'react';
import type { BarcodeInputProps } from './BarcodeInput';

export default function BarcodeScannerInput({
  onScan
}: Readonly<BarcodeInputProps>) {
  const [barcodeData, setBarcodeData] = useState<string>('');

  const onKeyPress = useCallback(
    (event: any) => {
      if (event.key === 'Enter') {
        onScan(barcodeData);
        setBarcodeData('');
      } else {
        setBarcodeData((barcode) => barcode + event.key);
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
