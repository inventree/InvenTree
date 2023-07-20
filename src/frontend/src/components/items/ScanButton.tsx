import { t } from '@lingui/macro';
import { ActionIcon } from '@mantine/core';
import { openContextModal } from '@mantine/modals';
import { IconQrcode } from '@tabler/icons-react';

export function ScanButton() {
  return (
    <ActionIcon
      onClick={() =>
        openContextModal({
          modal: 'qr',
          title: t`Scan QR code`,
          innerProps: {}
        })
      }
    >
      <IconQrcode />
    </ActionIcon>
  );
}
