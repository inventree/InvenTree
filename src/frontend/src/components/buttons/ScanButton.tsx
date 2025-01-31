import { t } from '@lingui/macro';
import { ActionIcon } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconQrcode } from '@tabler/icons-react';
import BarcodeScanDialog from '../barcodes/BarcodeScanDialog';

/**
 * A button which opens the QR code scanner modal
 */
export function ScanButton() {
  const [opened, { open, close }] = useDisclosure(false);

  return (
    <>
      <ActionIcon
        onClick={open}
        variant='transparent'
        title={t`Open Barcode Scanner`}
      >
        <IconQrcode />
      </ActionIcon>
      <BarcodeScanDialog opened={opened} onClose={close} />
    </>
  );
}
