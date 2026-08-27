import { useInvenTreeHotkeys } from '@lib/functions/Events';
import type { ModelType } from '@lib/index';
import { t } from '@lingui/core/macro';
import { ActionIcon, Tooltip } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconQrcode } from '@tabler/icons-react';
import { Suspense, lazy, useState } from 'react';
import type {
  BarcodeScanCallback,
  BarcodeScanSuccessCallback
} from '../barcodes/BarcodeScanDialog';

// Lazy loaded: ScanButton is rendered unconditionally in the nav Header (and
// elsewhere), but the scan dialog itself is only ever needed once a user
// actually opens it - deferring the import until first open (rather than
// just lazy-loading the component, which would still fetch it on every
// render) avoids pulling its dependency tree into every page load.
const BarcodeScanDialog = lazy(() => import('../barcodes/BarcodeScanDialog'));

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
  const [everOpened, setEverOpened] = useState(false);

  function handleOpen() {
    setEverOpened(true);
    open();
  }

  if (hotkey) {
    useInvenTreeHotkeys([
      [
        'mod+Shift+B',
        t`Open barcode scanner`,
        () => {
          handleOpen();
        }
      ]
    ]);
  }

  return (
    <>
      <Tooltip position='bottom-end' label={t`Scan Barcode`}>
        <ActionIcon
          aria-label={`barcode-scan-button-${modelType ?? 'any'}`}
          onClick={handleOpen}
          variant='transparent'
        >
          <IconQrcode />
        </ActionIcon>
      </Tooltip>
      {everOpened && (
        <Suspense fallback={null}>
          <BarcodeScanDialog
            opened={opened}
            modelType={modelType}
            callback={callback}
            onClose={close}
            onScanSuccess={onScanSuccess}
          />
        </Suspense>
      )}
    </>
  );
}
