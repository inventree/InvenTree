import { t } from '@lingui/macro';
import { Divider, Modal } from '@mantine/core';
import { useCallback } from 'react';
import { StylishText } from '../items/StylishText';
import { BarcodeInput } from './BarcodeInput';

export default function BarcodeScanDialog({
  title,
  opened,
  onClose
}: {
  title?: string;
  opened: boolean;
  onClose: () => void;
}) {
  const onScan = useCallback((barcode: string) => {
    // TODO
    console.log(`Scanned barcode: ${barcode}`);
  }, []);

  return (
    <>
      <Modal
        size='lg'
        opened={opened}
        onClose={onClose}
        title={<StylishText size='xl'>{title ?? t`Scan Barcode`}</StylishText>}
      >
        <Divider />
        <BarcodeInput onScan={onScan} />
      </Modal>
    </>
  );
}
