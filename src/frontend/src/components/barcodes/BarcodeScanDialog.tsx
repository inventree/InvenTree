import { t } from '@lingui/macro';
import { Box, Divider, Modal } from '@mantine/core';
import { useCallback, useState } from 'react';
import { type NavigateFunction, useNavigate } from 'react-router-dom';
import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import type { ModelType } from '../../enums/ModelType';
import { extractErrorMessage } from '../../functions/api';
import { getDetailUrl } from '../../functions/urls';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { StylishText } from '../items/StylishText';
import { ModelInformationDict } from '../render/ModelType';
import { BarcodeInput } from './BarcodeInput';

export default function BarcodeScanDialog({
  title,
  opened,
  onClose
}: Readonly<{
  title?: string;
  opened: boolean;
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
        <ScanInputHandler navigate={navigate} onClose={onClose} />
      </Box>
    </Modal>
  );
}
export function ScanInputHandler({
  onClose,
  navigate
}: Readonly<{ onClose: () => void; navigate: NavigateFunction }>) {
  const [error, setError] = useState<string>('');
  const [processing, setProcessing] = useState<boolean>(false);
  const user = useUserState();

  const onScan = useCallback((barcode: string) => {
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

  return <BarcodeInput onScan={onScan} error={error} processing={processing} />;
}
