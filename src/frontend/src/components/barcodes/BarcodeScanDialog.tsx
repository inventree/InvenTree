import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { getDetailUrl } from '@lib/functions/Navigation';
import { t } from '@lingui/core/macro';
import { Box, Divider, Modal } from '@mantine/core';
import { useCallback, useState } from 'react';
import { type NavigateFunction, useNavigate } from 'react-router-dom';
import { api } from '../../App';
import { extractErrorMessage } from '../../functions/api';
import { useUserState } from '../../states/UserState';
import { StylishText } from '../items/StylishText';
import { BarcodeInput } from './BarcodeInput';

export type BarcodeScanResult = {
  success: boolean;
  error: string;
};

// Callback function for handling a barcode scan
// This function should return true if the barcode was handled successfully
export type BarcodeScanCallback = (
  barcode: string,
  response: any
) => Promise<BarcodeScanResult>;

export default function BarcodeScanDialog({
  title,
  opened,
  callback,
  onClose
}: Readonly<{
  title?: string;
  opened: boolean;
  callback?: BarcodeScanCallback;
  onClose: () => void;
}>) {
  const navigate = useNavigate();

  return (
    <Modal
      size='lg'
      opened={opened}
      onClose={onClose}
      title={<StylishText size='xl'>{title ?? t`Scan Barcode`}</StylishText>}
    >
      <Divider />
      <Box>
        <ScanInputHandler
          navigate={navigate}
          onClose={onClose}
          callback={callback}
        />
      </Box>
    </Modal>
  );
}

export function ScanInputHandler({
  callback,
  onClose,
  navigate
}: Readonly<{
  callback?: BarcodeScanCallback;
  onClose: () => void;
  navigate: NavigateFunction;
}>) {
  const [error, setError] = useState<string>('');
  const [processing, setProcessing] = useState<boolean>(false);
  const user = useUserState();

  const defaultScan = useCallback((barcode: string) => {
    if (!barcode || barcode.length === 0) {
      return;
    }

    setProcessing(true);

    api
      .post(apiUrl(ApiEndpoints.barcode), {
        barcode: barcode
      })
      .then((response) => {
        setError('');

        const data = response.data ?? {};
        let match = false;

        // Find the matching model type
        for (const model_type of Object.keys(ModelInformationDict)) {
          if (data[model_type]?.['pk']) {
            if (user.hasViewPermission(model_type as ModelType)) {
              const url = getDetailUrl(
                model_type as ModelType,
                data[model_type]['pk']
              );
              onClose();
              navigate(url);
              match = true;
              break;
            }
          }
        }

        if (!match) {
          setError(t`No matching item found`);
        }
      })
      .catch((error) => {
        const _error = extractErrorMessage({
          error: error,
          field: 'error',
          defaultMessage: t`Failed to scan barcode`
        });

        setError(_error);
      })
      .finally(() => {
        setProcessing(false);
      });
  }, []);

  const onScan = useCallback(
    (barcode: string) => {
      if (callback) {
        // If a callback is provided, use it to handle the scan
        setProcessing(true);
        setError('');

        callback(barcode, {})
          .then((result) => {
            if (result.success) {
              onClose();
            } else {
              setError(result.error);
            }
          })
          .finally(() => {
            setProcessing(false);
          });
      } else {
        // If no callback is provided, use the default scan function
        defaultScan(barcode);
      }
    },
    [callback, defaultScan]
  );

  return <BarcodeInput onScan={onScan} error={error} processing={processing} />;
}

export function useBarcodeScanDialog({
  title,
  callback
}: Readonly<{
  title: string;
  callback: BarcodeScanCallback;
}>) {
  const [opened, setOpened] = useState(false);

  const open = useCallback((callback?: BarcodeScanCallback) => {
    setOpened(true);
  }, []);

  const dialog = (
    <BarcodeScanDialog
      title={title}
      opened={opened}
      callback={callback}
      onClose={() => setOpened(false)}
    />
  );

  return {
    open,
    dialog
  };
}
