import { Trans, t } from '@lingui/macro';
import { ActionIcon, Button, Group, Select, Space, Stack } from '@mantine/core';
import { Badge, Container } from '@mantine/core';
import { randomId, useLocalStorage } from '@mantine/hooks';
import { useDocumentVisibility } from '@mantine/hooks';
import { showNotification } from '@mantine/notifications';
import {
  IconPlayerPlayFilled,
  IconPlayerStopFilled
} from '@tabler/icons-react';
import { IconX } from '@tabler/icons-react';
import { Html5Qrcode } from 'html5-qrcode';
import { CameraDevice } from 'html5-qrcode/camera/core';
import React from 'react';
import { useEffect, useState } from 'react';

import { ModelType } from '../../enums/ModelType';
import { IS_DEV_OR_DEMO } from '../../main';

// Scan Item
interface ScanItem {
  id: string;
  ref: string;
  data: any;
  instance?: any;
  timestamp: Date;
  source: string;
  link?: string;
  model?: ModelType;
  pk?: string;
}

// Region input stuff
enum InputMethod {
  Manual = 'manually',
  ImageBarcode = 'imageBarcode'
}

interface inputProps {
  action: (items: ScanItem) => void;
}

/* Input that uses QR code detection from images */
export default function BarcodeInputImage({ action }: inputProps) {
  const [qrCodeScanner, setQrCodeScanner] = useState<Html5Qrcode | null>(null);
  const [camId, setCamId] = useLocalStorage<CameraDevice | null>({
    key: 'camId',
    defaultValue: null
  });
  const [cameras, setCameras] = useState<any[]>([]);
  const [cameraValue, setCameraValue] = useState<string | null>(null);
  const [ScanningEnabled, setIsScanning] = useState<boolean>(false);
  const [wasAutoPaused, setWasAutoPaused] = useState<boolean>(false);
  const documentState = useDocumentVisibility();

  let lastValue: string = '';

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
    if (ScanningEnabled && documentState === 'hidden') {
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
    action({
      id: randomId(),
      ref: decodedText,
      data: decodedText,
      timestamp: new Date(),
      source: InputMethod.ImageBarcode
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

  // button handlers
  function btnSelectCamera() {
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

  function btnStartScanning() {
    if (camId && qrCodeScanner && !ScanningEnabled) {
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
      setIsScanning(true);
    }
  }

  function btnStopScanning() {
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

  // on value change
  useEffect(() => {
    if (cameraValue === null) return;
    if (cameraValue === camId?.id) {
      console.log('matching value and id');
      return;
    }

    const cam = cameras.find((cam) => cam.id === cameraValue);

    // stop scanning if cam changed while scanning
    if (qrCodeScanner && ScanningEnabled) {
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

  return (
    <Stack spacing="xs">
      <Group spacing="xs">
        <Select
          value={cameraValue}
          onChange={setCameraValue}
          data={cameras.map((device) => {
            return { value: device.id, label: device.label };
          })}
          size="sm"
        />
        {ScanningEnabled ? (
          <ActionIcon onClick={btnStopScanning} title={t`Stop scanning`}>
            <IconPlayerStopFilled />
          </ActionIcon>
        ) : (
          <ActionIcon
            onClick={btnStartScanning}
            title={t`Start scanning`}
            disabled={!camId}
          >
            <IconPlayerPlayFilled />
          </ActionIcon>
        )}
        <Space sx={{ flex: 1 }} />
        <Badge color={ScanningEnabled ? 'green' : 'orange'}>
          {ScanningEnabled ? t`Scanning` : t`Not scanning`}
        </Badge>
      </Group>
      <Container px={0} id="reader" w={'100%'} mih="300px" />
      {!camId && (
        <Button onClick={btnSelectCamera}>
          <Trans>Select Camera</Trans>
        </Button>
      )}
    </Stack>
  );
}
