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
  onScanSuccess
}: {
  modelType?: ModelType;
  callback?: BarcodeScanCallback;
  onScanSuccess?: BarcodeScanSuccessCallback;
}) {
  const [opened, { open, close }] = useDisclosure(false);

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
