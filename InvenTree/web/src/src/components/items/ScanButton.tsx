import { ActionIcon } from "@mantine/core";
import { openContextModal } from "@mantine/modals";
import { IconQrcode } from '@tabler/icons';
import { t } from '@lingui/macro'


export function ScanButton() {
    return (
        <ActionIcon
            onClick={() => openContextModal({
                modal: 'qr',
                title: t`Scan QR code`,
                innerProps: {},
            })}
        >
            <IconQrcode size={16} />
        </ActionIcon>);
}
