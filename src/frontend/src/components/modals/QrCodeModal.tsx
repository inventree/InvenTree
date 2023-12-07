import { Trans, t } from '@lingui/macro';
import {
  Badge,
  Button,
  Container,
  Group,
  ScrollArea,
  Space,
  Stack,
  Text
} from '@mantine/core';
import {
  useDocumentVisibility,
  useListState,
  useLocalStorage
} from '@mantine/hooks';
import { ContextModalProps } from '@mantine/modals';
import { showNotification } from '@mantine/notifications';
import { IconX } from '@tabler/icons-react';
import { Html5Qrcode } from 'html5-qrcode';
import { CameraDevice } from 'html5-qrcode/camera/core';
import { Html5QrcodeResult } from 'html5-qrcode/core';
import { useEffect, useState } from 'react';

import { api } from '../../App';
import { ApiPaths } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';

export function QrCodeModal({
  context,
  id
}: ContextModalProps<{ modalBody: string }>) {
  const [qrCodeScanner, setQrCodeScanner] = useState<Html5Qrcode | null>(null);
  const [camId, setCamId] = useLocalStorage<CameraDevice | null>({
    key: 'camId',
    defaultValue: null
  });
  const [ScanningEnabled, setIsScanning] = useState<boolean>(false);
  const [wasAutoPaused, setWasAutoPaused] = useState<boolean>(false);
  const documentState = useDocumentVisibility();

  const [values, handlers] = useListState<string>([]);

  // Mount QR code once we are loaded
  useEffect(() => {
    setQrCodeScanner(new Html5Qrcode('reader'));
  }, []);

  // Stop/star when leaving or reentering page
  useEffect(() => {
    if (ScanningEnabled && documentState === 'hidden') {
      stopScanning();
      setWasAutoPaused(true);
    } else if (wasAutoPaused && documentState === 'visible') {
      startScanning();
      setWasAutoPaused(false);
    }
  }, [documentState]);

  // Scanner functions
  function onScanSuccess(
    decodedText: string,
    decodedResult: Html5QrcodeResult
  ) {
    qrCodeScanner?.pause();

    handlers.append(decodedText);
    api
      .post(apiUrl(ApiPaths.barcode), { barcode: decodedText })
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

    qrCodeScanner?.resume();
  }

  function onScanFailure(error: string) {
    if (
      error !=
      'QR code parse error, error = NotFoundException: No MultiFormat Readers were able to detect the code.'
    ) {
      console.warn(`Code scan error = ${error}`);
    }
  }

  function selectCamera() {
    Html5Qrcode.getCameras()
      .then((devices) => {
        if (devices?.length) {
          setCamId(devices[0]);
        }
      })
      .catch((err) => {
        showNotification({
          title: t`Error while getting camera`,
          message: err,
          color: 'red',
          icon: <IconX />
        });
      });
  }

  function startScanning() {
    if (camId && qrCodeScanner) {
      qrCodeScanner
        .start(
          camId.id,
          { fps: 10, qrbox: { width: 250, height: 250 } },
          (decodedText, decodedResult) => {
            onScanSuccess(decodedText, decodedResult);
          },
          (errorMessage) => {
            onScanFailure(errorMessage);
          }
        )
        .catch((err: string) => {
          showNotification({
            title: t`Error while scanning`,
            message: err,
            color: 'red',
            icon: <IconX />
          });
        });
      setIsScanning(true);
    }
  }

  function stopScanning() {
    if (qrCodeScanner && ScanningEnabled) {
      qrCodeScanner.stop().catch((err: string) => {
        showNotification({
          title: t`Error while stopping`,
          message: err,
          color: 'red',
          icon: <IconX />
        });
      });
      setIsScanning(false);
    }
  }

  return (
    <Stack>
      <Group>
        <Text size="sm">{camId?.label}</Text>
        <Space sx={{ flex: 1 }} />
        <Badge>{ScanningEnabled ? t`Scanning` : t`Not scanning`}</Badge>
      </Group>
      <Container px={0} id="reader" w={'100%'} mih="300px" />
      {!camId ? (
        <Button onClick={() => selectCamera()}>
          <Trans>Select Camera</Trans>
        </Button>
      ) : (
        <>
          <Group>
            <Button
              sx={{ flex: 1 }}
              onClick={() => startScanning()}
              disabled={camId != undefined && ScanningEnabled}
            >
              <Trans>Start scanning</Trans>
            </Button>
            <Button
              sx={{ flex: 1 }}
              onClick={() => stopScanning()}
              disabled={!ScanningEnabled}
            >
              <Trans>Stop scanning</Trans>
            </Button>
          </Group>
          {values.length == 0 ? (
            <Text color={'grey'}>
              <Trans>No scans yet!</Trans>
            </Text>
          ) : (
            <ScrollArea sx={{ height: 200 }} type="auto" offsetScrollbars>
              {values.map((value, index) => (
                <div key={index}>{value}</div>
              ))}
            </ScrollArea>
          )}
        </>
      )}
      <Button
        fullWidth
        mt="md"
        color="red"
        onClick={() => {
          stopScanning();
          context.closeModal(id);
        }}
      >
        <Trans>Close modal</Trans>
      </Button>
    </Stack>
  );
}
