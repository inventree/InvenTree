import { Trans, t } from '@lingui/macro';
import {
  ActionIcon,
  AspectRatio,
  Button,
  Card,
  Group,
  LoadingOverlay,
  Select,
  Space,
  Stack
} from '@mantine/core';
import { Badge, Container } from '@mantine/core';
import { randomId, useLocalStorage } from '@mantine/hooks';
import { useDocumentVisibility } from '@mantine/hooks';
import { showNotification } from '@mantine/notifications';
import {
  IconPlayerPlayFilled,
  IconPlayerStopFilled
} from '@tabler/icons-react';
import { IconX } from '@tabler/icons-react';
import { Html5Qrcode, Html5QrcodeCameraScanConfig } from 'html5-qrcode';
import { CameraDevice } from 'html5-qrcode/camera/core';
import { useEffect, useState } from 'react';

import { ScanItem } from './ScanPage.interface';

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
  const [ScannerLoading, setScannerLoading] = useState<boolean>(false);
  const [wasAutoPaused, setWasAutoPaused] = useState<boolean>(false);
  const documentState = useDocumentVisibility();

  let lastValue: string = '';

  const qrScannerOptions: Html5QrcodeCameraScanConfig = {
    fps: 10,
    qrbox: { width: 250, height: 250 }
  };

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
      stopScanning();
      setWasAutoPaused(true);
    } else if (wasAutoPaused && documentState === 'visible') {
      startScanning();
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
      showNotification({
        title: t`Error while scanning`,
        message: error,
        color: 'red',
        icon: <IconX />
      });
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

  const startScanning = async () => {
    setScannerLoading(true);
    if (camId && qrCodeScanner && !ScanningEnabled) {
      try {
        await qrCodeScanner.start(
          camId.id,
          qrScannerOptions,
          (decodedText) => onScanSuccess(decodedText),
          (errorMessage) => onScanFailure(errorMessage)
        );
        setIsScanning(true);
      } catch (error) {
        console.warn(`Error while starting QR Scanner.\n`, error);
        showNotification({
          title: t`Error while scanning`,
          message: `${error}`,
          color: 'red',
          icon: <IconX />
        });
        setIsScanning(false);
      }
      setScannerLoading(false);
    }
  };

  const stopScanning = async () => {
    if (qrCodeScanner && ScanningEnabled) {
      try {
        await qrCodeScanner.stop();
        setIsScanning(false);
      } catch (error) {
        console.warn(`Error while stopping QR Scanner.\n`, error);
        showNotification({
          title: t`Error while stopping`,
          message: `${error}`,
          color: 'red',
          icon: <IconX />
        });
        setIsScanning(false);
      }
    }
  };

  // on value change
  useEffect(() => {
    if (cameraValue === null) return;
    if (cameraValue === camId?.id) {
      console.log('matching value and id');
      return;
    }

    const cam = cameras.find((cam) => cam.id === cameraValue);

    // restart scanning if cam changed while scanning
    if (qrCodeScanner && ScanningEnabled) {
      // Fire & Forget - restart scanning async
      (async () => {
        await stopScanning();
        setCamId(cam);
        await startScanning();
      })();
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
          <ActionIcon onClick={stopScanning} title={t`Stop scanning`}>
            <IconPlayerStopFilled />
          </ActionIcon>
        ) : (
          <ActionIcon
            onClick={startScanning}
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
      <Card>
        <AspectRatio ratio={4 / 3} mx={'auto'}>
          <div>
            <LoadingOverlay visible={ScannerLoading} />
            {!ScannerLoading && !ScanningEnabled && (
              <Badge color="yellow">Scanner Stopped</Badge>
            )}
          </div>
          <div>
            <Container px={0} id="reader" w={'100%'} mih="300px" />
          </div>
        </AspectRatio>
      </Card>
      {!camId && (
        <Button onClick={btnSelectCamera}>
          <Trans>Select Camera</Trans>
        </Button>
      )}
    </Stack>
  );
}
