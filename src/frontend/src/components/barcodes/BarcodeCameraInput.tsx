import { t } from '@lingui/macro';
import { ActionIcon, Container, Group, Select, Stack } from '@mantine/core';
import { useDocumentVisibility, useLocalStorage } from '@mantine/hooks';
import { showNotification } from '@mantine/notifications';
import {
  IconCamera,
  IconPlayerPlayFilled,
  IconPlayerStopFilled,
  IconX
} from '@tabler/icons-react';
import { type CameraDevice, Html5Qrcode } from 'html5-qrcode';
import { useEffect, useState } from 'react';
import Expand from '../items/Expand';
import type { BarcodeInputProps } from './BarcodeInput';

export default function BarcodeCameraInput({
  onScan
}: Readonly<BarcodeInputProps>) {
  const [qrCodeScanner, setQrCodeScanner] = useState<Html5Qrcode | null>(null);
  const [camId, setCamId] = useLocalStorage<CameraDevice | null>({
    key: 'camId',
    defaultValue: null
  });
  const [cameras, setCameras] = useState<any[]>([]);
  const [cameraValue, setCameraValue] = useState<string | null>(null);
  const [scanningEnabled, setScanningEnabled] = useState<boolean>(false);
  const [wasAutoPaused, setWasAutoPaused] = useState<boolean>(false);
  const documentState = useDocumentVisibility();

  let lastValue = '';

  // Mount QR code once we are loaded
  useEffect(() => {
    setQrCodeScanner(new Html5Qrcode('reader'));

    // load cameras
    Html5Qrcode.getCameras().then((devices) => {
      if (devices?.length) {
        setCameras(devices);
      }
    });
  }, []);

  // set camera value from id
  useEffect(() => {
    if (camId) {
      setCameraValue(camId.id);
    }
  }, [camId]);

  // Stop/start when leaving or reentering page
  useEffect(() => {
    if (scanningEnabled && documentState === 'hidden') {
      btnStopScanning();
      setWasAutoPaused(true);
    } else if (wasAutoPaused && documentState === 'visible') {
      btnStartScanning();
      setWasAutoPaused(false);
    }
  }, [documentState]);

  // Scanner functions
  function onScanSuccess(decodedText: string) {
    qrCodeScanner?.pause();

    // dedouplication
    if (decodedText === lastValue) {
      qrCodeScanner?.resume();
      return;
    }
    lastValue = decodedText;

    // submit value upstream
    onScan?.(decodedText);

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

  function btnStartScanning() {
    if (camId && qrCodeScanner && !scanningEnabled) {
      qrCodeScanner
        .start(
          camId.id,
          { fps: 10, qrbox: { width: 250, height: 250 } },
          (decodedText) => {
            onScanSuccess(decodedText);
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
      setScanningEnabled(true);
    }
  }

  function btnStopScanning() {
    if (qrCodeScanner && scanningEnabled) {
      qrCodeScanner.stop().catch((err: string) => {
        showNotification({
          title: t`Error while stopping`,
          message: err,
          color: 'red',
          icon: <IconX />
        });
      });
      setScanningEnabled(false);
    }
  }

  // on value change
  useEffect(() => {
    if (cameraValue === null) return;
    if (cameraValue === camId?.id) {
      return;
    }

    const cam = cameras.find((cam) => cam.id === cameraValue);

    // stop scanning if cam changed while scanning
    if (qrCodeScanner && scanningEnabled) {
      // stop scanning
      qrCodeScanner.stop().then(() => {
        // change ID
        setCamId(cam);
        // start scanning
        qrCodeScanner.start(
          cam.id,
          { fps: 10, qrbox: { width: 250, height: 250 } },
          (decodedText) => {
            onScanSuccess(decodedText);
          },
          (errorMessage) => {
            onScanFailure(errorMessage);
          }
        );
      });
    } else {
      setCamId(cam);
    }
  }, [cameraValue]);

  const placeholder = t`Start scanning by selecting a camera and pressing the play button.`;

  return (
    <Stack gap='xs'>
      <Group gap='xs' preventGrowOverflow>
        <Expand>
          <Select
            leftSection={<IconCamera />}
            value={cameraValue}
            onChange={setCameraValue}
            data={cameras.map((device) => {
              return { value: device.id, label: device.label };
            })}
          />
        </Expand>

        {scanningEnabled ? (
          <ActionIcon
            size='lg'
            color='red'
            onClick={btnStopScanning}
            title={t`Stop scanning`}
            variant='transparent'
          >
            <IconPlayerStopFilled />
          </ActionIcon>
        ) : (
          <ActionIcon
            size='lg'
            color='green'
            onClick={btnStartScanning}
            title={t`Start scanning`}
            disabled={!camId}
            variant='transparent'
          >
            <IconPlayerPlayFilled />
          </ActionIcon>
        )}
      </Group>
      {scanningEnabled ? (
        <Container px={0} id='reader' w={'100%'} mih='300px' />
      ) : (
        <Container px={0} id='reader' w={'100%'}>
          {placeholder}
        </Container>
      )}
    </Stack>
  );
}
