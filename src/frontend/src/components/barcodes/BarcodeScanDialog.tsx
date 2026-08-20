import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { getDetailUrl } from '@lib/functions/Navigation';
import { t } from '@lingui/core/macro';
import { Box, Divider, Modal } from '@mantine/core';
import { hideNotification, showNotification } from '@mantine/notifications';
import { useCallback, useState } from 'react';
import { type NavigateFunction, useNavigate } from 'react-router-dom';
import { api } from '../../App';
import { extractErrorMessage } from '../../functions/api';
import { useUserState } from '../../states/UserState';
import { StylishText } from '../items/StylishText';
import { BarcodeInput } from './BarcodeInput';

export type BarcodeScanResult = {
  success?: string;
  error?: string;
};

export type BarcodeScanSuccessCallback = (
  barcode: string,
  response: any
) => void;

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
  modelType,
  onClose,
  onScanSuccess
}: Readonly<{
  title?: string;
  opened: boolean;
  modelType?: ModelType;
  callback?: BarcodeScanCallback;
  onClose: () => void;
  onScanSuccess?: BarcodeScanSuccessCallback;
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
          onScanSuccess={onScanSuccess}
          modelType={modelType}
          callback={callback}
        />
      </Box>
    </Modal>
  );
}

export function ScanInputHandler({
  callback,
  modelType,
  onClose,
  onScanSuccess,
  navigate
}: Readonly<{
  callback?: BarcodeScanCallback;
  onClose: () => void;
  onScanSuccess?: BarcodeScanSuccessCallback;
  modelType?: ModelType;
  navigate: NavigateFunction;
}>) {
  const [error, setError] = useState<string>('');
  const [processing, setProcessing] = useState<boolean>(false);
  const user = useUserState();

  const defaultScan = useCallback(
    (data: any) => {
      let match = false;

      // Find the matching model type
      for (const model_type of Object.keys(ModelInformationDict)) {
        // If a specific model type is provided, check if it matches
        if (modelType && model_type !== modelType) {
          continue;
        }

        if (data[model_type]?.['pk']) {
          if (user.hasViewPermission(model_type as ModelType)) {
            const url = getDetailUrl(
              model_type as ModelType,
              data[model_type]['pk']
            );
            onClose();

            if (onScanSuccess) {
              onScanSuccess(data['barcode'], data);
            } else {
              navigate(url);
            }

            match = true;
            break;
          }
        }
      }

      if (!match) {
        setError(t`No matching item found`);
      }
    },
    [navigate, onClose, user, modelType]
  );

  const onScan = useCallback(
    (barcode: string) => {
      if (!barcode || barcode.length === 0) {
        return;
      }

      setProcessing(true);
      setError('');

      api
        .post(apiUrl(ApiEndpoints.barcode), {
          barcode: barcode
        })
        .then((response: any) => {
          const data = response.data ?? {};

          if (callback && data.success && response.status === 200) {
            const instance = null;

            // If the caller is expecting a specific model type, check if it matches
            if (modelType) {
              const pk: number = data[modelType]?.['pk'];
              if (!pk) {
                setError(t`Barcode does not match the expected model type`);
                return;
              }
            }

            callback(barcode, data)
              .then((result: BarcodeScanResult) => {
                if (result.success) {
                  hideNotification('barcode-scan');
                  showNotification({
                    id: 'barcode-scan',
                    title: t`Success`,
                    message: result.success,
                    color: 'green'
                  });
                  onClose();
                } else {
                  setError(result.error ?? t`Failed to handle barcode`);
                }
              })
              .finally(() => {
                setProcessing(false);
              });
          } else {
            // If no callback is provided, use the default scan function
            defaultScan(data);
            setProcessing(false);
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
    },
    [callback, defaultScan, modelType, onClose]
  );

  return <BarcodeInput onScan={onScan} error={error} processing={processing} />;
}

export function useBarcodeScanDialog({
  title,
  callback,
  modelType
}: Readonly<{
  title: string;
  modelType?: ModelType;
  callback: BarcodeScanCallback;
}>) {
  const [opened, setOpened] = useState(false);

  const open = useCallback(() => {
    setOpened(true);
  }, []);

  const dialog = (
    <BarcodeScanDialog
      title={title}
      opened={opened}
      callback={callback}
      modelType={modelType}
      onClose={() => setOpened(false)}
    />
  );

  return {
    open,
    dialog
  };
}
