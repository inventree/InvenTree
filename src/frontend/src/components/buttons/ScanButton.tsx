import { t } from '@lingui/macro';
import { ActionIcon } from '@mantine/core';
import { openContextModal } from '@mantine/modals';
import { IconQrcode } from '@tabler/icons-react';

/**
 * A button which opens the QR code scanner modal
 */
export function ScanButton() {
  return (
    <ActionIcon
      onClick={() =>
        openContextModal({
          modal: 'qr',
          title: t`Scan Barcode`,
          innerProps: {}
        })
      }
      variant='transparent'
      title={t`Open Barcode Scanner`}
    >
      <IconQrcode />
    </ActionIcon>
  );
}
