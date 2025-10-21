import { t } from '@lingui/core/macro';
import { ActionIcon, Tooltip } from '@mantine/core';
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
      <Tooltip position='bottom-end' label={t`Scan Barcode`}>
        <ActionIcon
          onClick={open}
          variant='transparent'
          title={t`Open Barcode Scanner`}
        >
          <IconQrcode />
        </ActionIcon>
      </Tooltip>
      <BarcodeScanDialog opened={opened} onClose={close} />
    </>
  );
}
