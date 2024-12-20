import { t } from '@lingui/macro';
import { Divider, Modal } from '@mantine/core';
import { useCallback, useState } from 'react';
import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import type { ModelType } from '../../enums/ModelType';
import { extractErrorMessage } from '../../functions/api';
import { apiUrl } from '../../states/ApiState';
import { StylishText } from '../items/StylishText';
import { ModelInformationDict } from '../render/ModelType';
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
  const navigate = useNavigate();
  const user = useUserState();

  const [error, setError] = useState<string>('');

  const onScan = useCallback((barcode: string) => {
    // TODO
    console.log(`Scanned barcode: ${barcode}`);

    if (!barcode || barcode.length === 0) {
      return;
    }

    api
      .post(apiUrl(ApiEndpoints.barcode), {
        barcode: barcode
      })
      .then((response) => {
        setError('');

        const data = response.data ?? {};

        // Find the matching model type
        for (const model_type of Object.keys(ModelInformationDict)) {
          const model = ModelInformationDict[model_type as ModelType];

          if (data[model_type]?.[model_type]?.['pk']) {
            // TODO: Found a match!!!
          }
        }
      })
      .catch((error) => {
        const _error = extractErrorMessage({
          error: error,
          field: 'error',
          defaultMessage: t`Failed to scan barcode`
        });

        setError(_error);
      });
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
        <BarcodeInput onScan={onScan} error={error} />
      </Modal>
    </>
  );
}
