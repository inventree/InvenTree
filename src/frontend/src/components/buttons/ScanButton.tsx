import { useInvenTreeHotkeys } from '@lib/functions/Events';
import type { ModelType } from '@lib/index';
import { t } from '@lingui/core/macro';
import { ActionIcon, Tooltip } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconQrcode } from '@tabler/icons-react';
import BarcodeScanDialog, {
  type BarcodeScanCallback,
  type BarcodeScanSuccessCallback
} from '../barcodes/BarcodeScanDialog';

/**
 * A button which opens the QR code scanner modal
 */
export function ScanButton({
  modelType,
  callback,
  onScanSuccess,
  hotkey = false
}: {
  modelType?: ModelType;
  callback?: BarcodeScanCallback;
  onScanSuccess?: BarcodeScanSuccessCallback;
  hotkey?: boolean;
}) {
  const [opened, { open, close }] = useDisclosure(false);

  if (hotkey) {
    useInvenTreeHotkeys([
      [
        'mod+b',
        t`Open barcode scanner`,
        () => {
          open();
        }
      ]
    ]);
  }

  return (
    <>
      <Tooltip position='bottom-end' label={t`Scan Barcode`}>
        <ActionIcon
          aria-label={`barcode-scan-button-${modelType ?? 'any'}`}
          onClick={open}
          variant='transparent'
        >
          <IconQrcode />
        </ActionIcon>
      </Tooltip>
      <BarcodeScanDialog
        opened={opened}
        modelType={modelType}
        callback={callback}
        onClose={close}
        onScanSuccess={onScanSuccess}
      />
    </>
  );
}
