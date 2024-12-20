import { Box, Center, Container } from '@mantine/core';
import { IconScan } from '@tabler/icons-react';
import type { BarcodeInputProps } from './BarcodeInput';

export default function BarcodeScannerInput({
  onScan
}: Readonly<BarcodeInputProps>) {
  return (
    <>
      <Box>
        <Container>
          <Center>
            <IconScan size={48} />
          </Center>
        </Container>
      </Box>
    </>
  );
}
