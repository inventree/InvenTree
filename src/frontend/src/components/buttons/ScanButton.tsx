import { t } from '@lingui/macro';
import { ActionIcon } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { IconQrcode } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import type { ModelType } from '../../enums/ModelType';
import { getDetailUrl } from '../../functions/urls';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import type { ApiFormFieldSet } from '../forms/fields/ApiFormField';
import { ModelInformationDict } from '../render/ModelType';

/**
 * A button which opens the QR code scanner modal
 */
export function ScanButton() {
  const navigate = useNavigate();
  const [scanError, setScanError] = useState<string | null>(null);

  const fields: ApiFormFieldSet = useMemo(() => {
    return {
      barcode: {
        error: scanError || undefined,
        required: false
      }
    };
  }, [scanError]);

  const onScanSuccess = useCallback((data: any) => {
    let match = false;

    // Try to find a "match" for the scanned item
    for (const model_type of Object.keys(ModelInformationDict)) {
      const model = ModelInformationDict[model_type as ModelType];

      if (model && data[model_type] && data[model_type]?.pk) {
        // Found a match!
        const url = getDetailUrl(model_type as ModelType, data[model_type].pk);
        navigate(url);
        match = true;
        break;
      }
    }

    if (!match) {
      showNotification({
        title: t`No Match`,
        message: t`No matching item found for scanned barcode`,
        color: 'red'
      });
    }
  }, []);

  const quickScan = useCreateApiFormModal({
    title: t`Scan Barcode`,
    url: ApiEndpoints.barcode,
    fields: fields,
    successMessage: '',
    submitText: t`Scan`,
    focus: 'barcode',
    onFormSuccess: (data: any) => {
      onScanSuccess(data);
    },
    onFormError: (error: any) => {
      // Display error message
      const response: any = error?.response?.data;
      setScanError(response?.error ?? response?.barcode ?? null);
    }
  });

  return (
    <>
      <ActionIcon
        onClick={() => {
          quickScan.open();
        }}
        variant='transparent'
        title={t`Open Barcode Scanner`}
      >
        <IconQrcode />
      </ActionIcon>
      {quickScan.modal}
    </>
  );
}
