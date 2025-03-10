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
import { IconCamera, IconScan } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { useLocalStorage } from '@mantine/hooks';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { Boundary } from '../Boundary';
import BarcodeCameraInput from './BarcodeCameraInput';
import BarcodeKeyboardInput from './BarcodeKeyboardInput';

export type BarcodeInputProps = {
  onScan: (barcode: string) => void;
  processing?: boolean;
  error?: string;
  label?: string;
  actionText?: string;
};

export function BarcodeInput({
  onScan,
  error,
  processing,
  label = t`Barcode`,
  actionText = t`Scan`
}: Readonly<BarcodeInputProps>) {
  const globalSettings = useGlobalSettingsState();

  const [barcode, setBarcode] = useState<string>('');

  const [inputType, setInputType] = useLocalStorage<string | null>({
    key: 'barcodeInputType',
    defaultValue: 'scanner'
  });

  const scanningOptions: SegmentedControlItem[] = useMemo(() => {
    const options: SegmentedControlItem[] = [];

    if (globalSettings.isSet('BARCODE_WEBCAM_SUPPORT', true)) {
      options.push({
        value: 'camera',
        label: (
          <Tooltip label={t`Camera Input`}>
            <IconCamera size={20} aria-label='barcode-input-camera' />
          </Tooltip>
        )
      });
    }

    options.push({
      value: 'scanner',
      label: (
        <Tooltip label={t`Scanner Input`}>
          <IconScan size={20} aria-label='barcode-input-scanner' />
        </Tooltip>
      )
    });

    return options;
  }, [globalSettings]);

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
      default:
        return <BarcodeKeyboardInput onScan={onScanBarcode} />;
    }
  }, [inputType, onScan]);

  return (
    <Box>
      <Boundary label='BarcodeInput'>
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
      </Boundary>
    </Box>
  );
}
