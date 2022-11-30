import { ContextModalProps } from '@mantine/modals';
import { Text, Button, Group, Container, Stack, Code, Badge, Space } from '@mantine/core';
import { Trans, t } from '@lingui/macro';
import { Html5Qrcode } from "html5-qrcode";
import { Html5QrcodeResult } from "html5-qrcode/core";
import { CameraDevice } from "html5-qrcode/camera/core";
import { useEffect, useState } from 'react';
import { useDocumentVisibility, useLocalStorage } from '@mantine/hooks';
import { showNotification } from '@mantine/notifications';
import { IconX } from '@tabler/icons';

export function QrCodeModal({ context, id, innerProps }: ContextModalProps<{ modalBody: string }>) {
    const [qrCodeScanner, setQrCodeScanner] = useState<Html5Qrcode | null>(null);
    const [camId, setCamId] = useLocalStorage<CameraDevice | null>({ key: 'camId', defaultValue: null });
    const [ScanningEnabled, setIsScanning] = useState<boolean>(false);
    const [wasAutoPaused, setWasAutoPaused] = useState<boolean>(false);
    const documentState = useDocumentVisibility();

    // Mount QR code once we are loaded
    useEffect(() => { setQrCodeScanner(new Html5Qrcode("reader")); }, []);

    // Stop/star when leaving or reentering page
    useEffect(() => {
        if (ScanningEnabled && documentState === "hidden") {
            stopScan();
            setWasAutoPaused(true);
        } else if (wasAutoPaused && documentState === "visible") {
            mountScan();
            setWasAutoPaused(false);
        }
    }, [documentState]);

    function onScanSuccess(decodedText: string, decodedResult: Html5QrcodeResult) {
        console.log(`Code matched = ${decodedText}`, decodedResult);
    }

    function onScanFailure(error: string) {
        console.warn(`Code scan error = ${error}`);
    }

    function getCamera() {
        Html5Qrcode.getCameras().then(devices => {
            if (devices && devices.length) { setCamId(devices[0]); }
        }).catch(err => {
            showNotification({ title: t`Error while getting camera`, message: err, color: 'red', icon: <IconX size={18} /> })
        });
    }

    function mountScan() {
        if (camId && qrCodeScanner) {
            qrCodeScanner.start(
                camId.id,
                { fps: 10, qrbox: { width: 250, height: 250 } },
                (decodedText, decodedResult) => { onScanSuccess(decodedText, decodedResult) },
                (errorMessage) => { onScanFailure(errorMessage) })
                .catch((err: string) => {
                    showNotification({ title: t`Error while scanning`, message: err, color: 'red', icon: <IconX size={18} /> })
                });
            setIsScanning(true);
        }
    }

    function stopScan() {
        if (qrCodeScanner && ScanningEnabled) {
            qrCodeScanner.stop().catch((err: string) => {
                showNotification({ title: t`Error while stopping`, message: err, color: 'red', icon: <IconX size={18} /> })
            });
            setIsScanning(false);
        }
    }

    return (
        <Stack>
            <Group>
                <Text size='sm'>{camId?.label}</Text>
                <Space sx={{ flex: 1 }} />
                <Badge>{ScanningEnabled ? t`Scanning` : t`Not scanning`}</Badge>
            </Group>
            <Container px={0} id="reader" w={'100%'} mih='300px' />
            {(!camId) ? <Button onClick={() => getCamera()} ><Trans>Select Camera</Trans></Button> : null}
            <Group>
                <Button sx={{ flex: 1 }} onClick={() => mountScan()} disabled={(camId != undefined && ScanningEnabled == true)}><Trans>Start scanning</Trans></Button>
                <Button sx={{ flex: 1 }} onClick={() => stopScan()} disabled={!ScanningEnabled}><Trans>Stop scanning</Trans></Button>
            </Group>
            <Code>
                {JSON.stringify(camId)}
            </Code>
            <Button fullWidth mt="md" color="red" onClick={() => { stopScan(); context.closeModal(id) }}><Trans>Close modal</Trans></Button>
        </Stack >
    );
}
