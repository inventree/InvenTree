import { t } from '@lingui/macro';
import {
  Alert,
  Box,
  Card,
  Divider,
  LoadingOverlay,
  SegmentedControl,
  type SegmentedControlItem,
  Stack,
  Tooltip
} from '@mantine/core';
import { IconCamera, IconKeyboard, IconScan } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { useLocalStorage } from '@mantine/hooks';
import BarcodeCameraInput from './BarcodeCameraInput';
import BarcodeKeyboardInput from './BarcodeKeyboardInput';
import BarcodeScannerInput from './BarcodeScannerInput';

export type BarcodeInputProps = {
  onScan: (barcode: string) => void;
  error?: string;
  placeholder?: string;
  label?: string;
  actionText?: string;
  processing?: boolean;
};

export function BarcodeInput({
  onScan,
  error,
  processing,
  label = t`Barcode`,
  actionText = t`Scan`
}: Readonly<BarcodeInputProps>) {
  const [barcode, setBarcode] = useState<string>('');

  const [inputType, setInputType] = useLocalStorage<string | null>({
    key: 'barcodeInputType',
    defaultValue: 'scanner'
  });

  const scanningOptions: SegmentedControlItem[] = useMemo(() => {
    const options: SegmentedControlItem[] = [];

    options.push({
      value: 'scanner',
      label: (
        <Tooltip label={t`Scanner Input`}>
          <IconScan size={20} aria-label='barcode-input-scanner' />
        </Tooltip>
      )
    });

    // TODO : Hide camera input optionally
    options.push({
      value: 'camera',
      label: (
        <Tooltip label={t`Camera Input`}>
          <IconCamera size={20} aria-label='barcode-input-camera' />
        </Tooltip>
      )
    });

    options.push({
      value: 'keyboard',
      label: (
        <Tooltip label={t`Keyboard Input`}>
          <IconKeyboard size={20} aria-label='barcode-input-keyboard' />
        </Tooltip>
      )
    });

    return options;
  }, []);

  const onScanBarcode = useCallback(
    (barcode: string) => {
      setBarcode(barcode);
      onScan(barcode);
    },
    [onScan]
  );

  const scannerInput = useMemo(() => {
    switch (inputType) {
      case 'camera':
        return <BarcodeCameraInput onScan={onScanBarcode} />;
      case 'scanner':
        return <BarcodeScannerInput onScan={onScanBarcode} />;
      case 'keyboard':
      default:
        return <BarcodeKeyboardInput onScan={onScanBarcode} />;
    }
  }, [inputType, onScan]);

  return (
    <Box>
      <LoadingOverlay visible={processing} />
      <Stack gap='xs'>
        <SegmentedControl
          aria-label='barcode-input-type'
          size='xs'
          data={scanningOptions}
          value={inputType || 'scanner'}
          onChange={setInputType}
        />
        <Divider />
        <Card p='sm' withBorder>
          {barcode ? (
            <Alert color='blue' title={t`Barcode Data`} p='xs'>
              {barcode}
            </Alert>
          ) : (
            <Alert color='yellow' title={t`No barcode data`} p='xs'>
              {t`Scan or enter barcode data`}
            </Alert>
          )}
          {error && (
            <Alert color='red' title={t`Error`} p='xs'>
              {error}
            </Alert>
          )}
        </Card>

        <Card p='sm' withBorder>
          {scannerInput}
        </Card>
      </Stack>
    </Box>
  );
}
