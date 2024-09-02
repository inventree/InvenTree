import { Trans, t } from '@lingui/macro';
import { Button, ScrollArea, Stack, Text } from '@mantine/core';
import { useListState } from '@mantine/hooks';
import { ContextModalProps } from '@mantine/modals';
import { showNotification } from '@mantine/notifications';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';
import { BarcodeInput } from '../items/BarcodeInput';

export function QrCodeModal({
  context,
  id
}: Readonly<ContextModalProps<{ modalBody: string }>>) {
  const [values, handlers] = useListState<string>([]);

  function onScanAction(decodedText: string) {
    handlers.append(decodedText);
    api
      .post(apiUrl(ApiEndpoints.barcode), { barcode: decodedText })
      .then((response) => {
        showNotification({
          title: response.data?.success || t`Unknown response`,
          message: JSON.stringify(response.data),
          color: response.data?.success ? 'teal' : 'red'
        });
        if (response.data?.url) {
          window.location.href = response.data.url;
        }
      });
  }

  return (
    <Stack gap="xs">
      <BarcodeInput onScan={onScanAction} />
      {values.length == 0 ? (
        <Text c={'grey'}>
          <Trans>No scans yet!</Trans>
        </Text>
      ) : (
        <ScrollArea style={{ height: 200 }} type="auto" offsetScrollbars>
          {values.map((value, index) => (
            <div key={`${index}-${value}`}>{value}</div>
          ))}
        </ScrollArea>
      )}
      <Button
        fullWidth
        mt="md"
        color="red"
        onClick={() => {
          // stopScanning();
          context.closeModal(id);
        }}
      >
        <Trans>Close modal</Trans>
      </Button>
    </Stack>
  );
}
