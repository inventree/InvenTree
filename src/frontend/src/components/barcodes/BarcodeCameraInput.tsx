import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Container,
  Group,
  Select,
  Stack,
  Tooltip
} from '@mantine/core';
import { useDocumentVisibility, useLocalStorage } from '@mantine/hooks';
import { showNotification } from '@mantine/notifications';
import {
  IconBulb,
  IconBulbOff,
  IconCamera,
  IconPlayerPlayFilled,
  IconPlayerStopFilled,
  IconX
} from '@tabler/icons-react';
import { type CameraDevice, Html5Qrcode } from 'html5-qrcode';
import { useEffect, useRef, useState } from 'react';
import Expand from '../items/Expand';
import type { BarcodeInputProps } from './BarcodeInput';

/*
 * Native browser barcode detection (Shape Detection API).
 *
 * Backed by the OS / hardware-accelerated decoder (Android ML Kit / Google
 * Play Services, macOS Vision, Windows platform decoder) and therefore much
 * faster and far more robust to poor lighting, blur and small codes than the
 * pure-JS `html5-qrcode` fallback (which decodes in software on the CPU).
 *
 * We always prefer the native detector when available and only fall back to
 * `html5-qrcode` for browsers that do not implement the Shape Detection API
 * (e.g. Firefox, iOS Safari).
 */
interface NativeDetectedBarcode {
  rawValue: string;
  format: string;
  boundingBox: DOMRectReadOnly;
  cornerPoints: { x: number; y: number }[];
}

interface NativeBarcodeDetector {
  detect(source: CanvasImageSource): Promise<NativeDetectedBarcode[]>;
}

declare global {
  interface Window {
    BarcodeDetector?: new (options?: {
      formats?: string[];
    }) => NativeBarcodeDetector;
  }
}

// Interval between native detection attempts. Native decoding is hardware
// accelerated and detection runs over the full frame (no aiming box), so this
// feels much faster than the legacy 10fps software loop while staying gentle
// on the CPU.
const NATIVE_DETECT_INTERVAL_MS = 100;

function getNativeDetector(): NativeBarcodeDetector | null {
  try {
    if (typeof window === 'undefined' || !('BarcodeDetector' in window)) {
      return null;
    }
    const Detector = window.BarcodeDetector;
    if (!Detector) return null;
    // Do not pass an explicit format list: the browser then detects every
    // format it supports. Passing a list that includes an unsupported format
    // throws in some browsers, which would silently disable native scanning.
    return new Detector();
  } catch {
    return null;
  }
}

export default function BarcodeCameraInput({
  onScan
}: Readonly<BarcodeInputProps>) {
  const nativeDetectorRef = useRef<NativeBarcodeDetector | null>(null);
  const [useNative, setUseNative] = useState(false);

  const [camId, setCamId] = useLocalStorage<CameraDevice | null>({
    key: 'camId',
    defaultValue: null
  });
  const [cameras, setCameras] = useState<any[]>([]);
  const [cameraValue, setCameraValue] = useState<string | null>(null);
  const [scanningEnabled, setScanningEnabled] = useState<boolean>(false);
  const [torchSupported, setTorchSupported] = useState<boolean>(false);
  const [torchOn, setTorchOn] = useState<boolean>(false);
  const [wasAutoPaused, setWasAutoPaused] = useState<boolean>(false);
  const documentState = useDocumentVisibility();

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const detectTimerRef = useRef<number | null>(null);
  const detectingRef = useRef<boolean>(false);
  const lastValueRef = useRef<string>('');

  // Legacy software scanner (fallback only)
  const legacyScannerRef = useRef<Html5Qrcode | null>(null);

  // Detect native support + load camera list once
  useEffect(() => {
    const detector = getNativeDetector();
    nativeDetectorRef.current = detector;
    setUseNative(detector !== null);

    if (!detector) {
      legacyScannerRef.current = new Html5Qrcode('reader');
    }

    Html5Qrcode.getCameras().then((devices) => {
      if (devices?.length) {
        setCameras(devices);

        // Auto-select a camera so the play button is immediately usable,
        // preferring the rear/back camera (better autofocus + resolution).
        if (!camId) {
          const preferred =
            devices.find((device) =>
              /back|rear|environment|后置|后/i.test(device.label || '')
            ) || devices[0];
          setCamId(preferred);
        }
      }
    });
  }, []);

  // Set camera value from saved id
  useEffect(() => {
    if (camId) {
      setCameraValue(camId.id);
    }
  }, [camId]);

  // Cleanup native resources on unmount
  useEffect(() => {
    return () => {
      if (detectTimerRef.current !== null) {
        window.clearInterval(detectTimerRef.current);
      }
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  // Stop/start when leaving or reentering the page
  useEffect(() => {
    if (scanningEnabled && documentState === 'hidden') {
      btnStopScanning();
      setWasAutoPaused(true);
    } else if (wasAutoPaused && documentState === 'visible') {
      btnStartScanning();
      setWasAutoPaused(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentState]);

  // Common result handling with consecutive-duplicate suppression
  function handleScanResult(value: string) {
    if (!value || value === lastValueRef.current) return;
    lastValueRef.current = value;
    onScan?.(value);
  }

  // --- Native (BarcodeDetector) path ---

  async function startNativeScanning(device?: CameraDevice) {
    const target = device ?? camId;
    if (!target || !videoRef.current) return;

    try {
      const constraints: MediaStreamConstraints = {
        video: {
          facingMode: { ideal: 'environment' },
          ...(target.id ? { deviceId: { ideal: target.id } } : {}),
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        },
        audio: false
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;
      videoRef.current.srcObject = stream;
      await videoRef.current.play();

      const track = stream.getVideoTracks()[0];
      if (track && typeof track.getCapabilities === 'function') {
        const caps = track.getCapabilities() as MediaTrackCapabilities & {
          torch?: boolean;
        };
        setTorchSupported(!!caps.torch);
      }

      setScanningEnabled(true);
      setTorchOn(false);
      startNativeDetectLoop();
    } catch (err) {
      showNotification({
        title: t`Error while scanning`,
        message: String(err),
        color: 'red',
        icon: <IconX />
      });
    }
  }

  function stopNativeScanning() {
    if (detectTimerRef.current !== null) {
      window.clearInterval(detectTimerRef.current);
      detectTimerRef.current = null;
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setScanningEnabled(false);
    setTorchOn(false);
    setTorchSupported(false);
  }

  function startNativeDetectLoop() {
    if (detectTimerRef.current !== null) {
      window.clearInterval(detectTimerRef.current);
    }
    detectTimerRef.current = window.setInterval(() => {
      void detectOnce();
    }, NATIVE_DETECT_INTERVAL_MS);
  }

  async function detectOnce() {
    if (detectingRef.current) return;
    const detector = nativeDetectorRef.current;
    const video = videoRef.current;
    if (!detector || !video || video.readyState < 2) return;

    detectingRef.current = true;
    try {
      const results = await detector.detect(video);
      if (results?.length) {
        for (const result of results) {
          if (result?.rawValue) {
            handleScanResult(result.rawValue);
          }
        }
      }
    } catch {
      // Per-frame decode failures are expected (e.g. no code currently in view).
    } finally {
      detectingRef.current = false;
    }
  }

  async function toggleTorch() {
    const track = streamRef.current?.getVideoTracks()[0];
    if (!track) return;
    try {
      await track.applyConstraints({
        advanced: [{ torch: !torchOn }]
      } as unknown as MediaTrackConstraints);
      setTorchOn(!torchOn);
    } catch {
      showNotification({
        title: t`Flashlight`,
        message: t`Flashlight control is not supported on this device`,
        color: 'yellow'
      });
    }
  }

  // --- Legacy (html5-qrcode) fallback path ---

  function startLegacyScanning(device?: CameraDevice) {
    const target = device ?? camId;
    const scanner = legacyScannerRef.current;
    if (target && scanner && !scanningEnabled) {
      scanner
        .start(
          target.id,
          {
            fps: 15,
            qrbox: { width: 300, height: 300 },
            aspectRatio: 1.0,
            videoConstraints: { facingMode: 'environment' }
          },
          (decodedText) => {
            scanner.pause();
            handleScanResult(decodedText);
            scanner.resume();
          },
          (errorMessage) => {
            if (
              errorMessage !=
              'QR code parse error, error = NotFoundException: No MultiFormat Readers were able to detect the code.'
            ) {
              console.warn(`Code scan error = ${errorMessage}`);
            }
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

  function stopLegacyScanning() {
    const scanner = legacyScannerRef.current;
    if (scanner && scanningEnabled) {
      scanner.stop().catch((err: string) => {
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

  function btnStartScanning() {
    if (useNative) {
      void startNativeScanning();
    } else {
      startLegacyScanning();
    }
  }

  function btnStopScanning() {
    if (useNative) {
      stopNativeScanning();
    } else {
      stopLegacyScanning();
    }
  }

  // Restart when the selected camera changes while scanning
  useEffect(() => {
    if (cameraValue === null || cameraValue === camId?.id) return;
    const cam = cameras.find((camera) => camera.id === cameraValue);
    if (!cam) return;

    const wasScanning = scanningEnabled;
    if (wasScanning) {
      btnStopScanning();
    }
    setCamId(cam);
    if (wasScanning) {
      if (useNative) {
        void startNativeScanning(cam);
      } else {
        startLegacyScanning(cam);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

        {useNative && scanningEnabled && torchSupported && (
          <Tooltip
            label={torchOn ? t`Turn off flashlight` : t`Turn on flashlight`}
          >
            <ActionIcon
              size='lg'
              variant='transparent'
              color={torchOn ? 'yellow' : 'gray'}
              onClick={() => void toggleTorch()}
              title={torchOn ? t`Turn off flashlight` : t`Turn on flashlight`}
            >
              {torchOn ? <IconBulb /> : <IconBulbOff />}
            </ActionIcon>
          </Tooltip>
        )}

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

      {useNative ? (
        <Container px={0} w='100%'>
          <video
            ref={videoRef}
            muted
            playsInline
            style={{
              width: '100%',
              borderRadius: 8,
              display: scanningEnabled ? 'block' : 'none'
            }}
          />
          {!scanningEnabled && <div>{placeholder}</div>}
        </Container>
      ) : (
        <Container
          px={0}
          id='reader'
          w='100%'
          mih={scanningEnabled ? '300px' : undefined}
        >
          {!scanningEnabled && placeholder}
        </Container>
      )}
    </Stack>
  );
}
