import { StylishText } from '@lib/components/StylishText';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { getDetailUrl } from '@lib/functions/Navigation';
import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Badge,
  Box,
  Button,
  Checkbox,
  Divider,
  Group,
  Modal,
  ScrollArea,
  Stack,
  Text,
  ThemeIcon,
  Timeline,
  Tooltip
} from '@mantine/core';
import { hideNotification, showNotification } from '@mantine/notifications';
import {
  IconCheck,
  IconCircleX,
  IconTrash,
  IconX
} from '@tabler/icons-react';
import { useCallback, useRef, useState } from 'react';
import { type NavigateFunction, useNavigate } from 'react-router-dom';
import { api } from '../../App';
import { extractErrorMessage } from '../../functions/api';
import { useUserState } from '../../states/UserState';
import { BarcodeInput } from './BarcodeInput';

export type BarcodeScanResult = {
  success?: string;
  error?: string;
};

export type BarcodeScanSuccessCallback = (
  barcode: string,
  response: any
) => void;

// Callback function for handling a barcode scan.
// Returns a BarcodeScanResult. In continuous mode the dialog stays open after
// a successful scan so users can scan the next item without touching the UI.
export type BarcodeScanCallback = (
  barcode: string,
  response: any
) => Promise<BarcodeScanResult>;

// --------------------------------------------------------------------------
// Represents one completed scan entry shown in the continuous scan log
// --------------------------------------------------------------------------
interface ScanLogEntry {
  id: string; // uniquely identifies entry for key prop
  barcode: string;
  label: string; // human-readable description of what was matched
  success: boolean;
  message: string;
}

// --------------------------------------------------------------------------
// BarcodeScanDialog
// --------------------------------------------------------------------------
export default function BarcodeScanDialog({
  title,
  opened,
  callback,
  modelType,
  onClose,
  onScanSuccess,
  continuous = false
}: Readonly<{
  title?: string;
  opened: boolean;
  modelType?: ModelType;
  callback?: BarcodeScanCallback;
  onClose: () => void;
  onScanSuccess?: BarcodeScanSuccessCallback;
  /** When true, the dialog stays open for repeated scans and shows a running
   * log of all completed scans. A "Done" button closes the dialog. */
  continuous?: boolean;
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
        <ScanInputHandler
          navigate={navigate}
          onClose={onClose}
          onScanSuccess={onScanSuccess}
          modelType={modelType}
          callback={callback}
          continuous={continuous}
        />
      </Box>
    </Modal>
  );
}

// --------------------------------------------------------------------------
// ScanInputHandler — owns all scan state
// --------------------------------------------------------------------------
export function ScanInputHandler({
  callback,
  modelType,
  onClose,
  onScanSuccess,
  navigate,
  continuous: continuousProp = false
}: Readonly<{
  callback?: BarcodeScanCallback;
  onClose: () => void;
  onScanSuccess?: BarcodeScanSuccessCallback;
  modelType?: ModelType;
  navigate: NavigateFunction;
  continuous?: boolean;
}>) {
  const [error, setError] = useState<string>('');
  const [processing, setProcessing] = useState<boolean>(false);
  const [scanLog, setScanLog] = useState<ScanLogEntry[]>([]);

  // Continuous mode can be toggled per-session by the user (starts from the
  // prop value, but the checkbox lets them turn it on/off mid-session).
  const [continuous, setContinuous] = useState<boolean>(continuousProp);

  // Ref so the scan counter survives re-renders without causing them
  const scanCounter = useRef<number>(0);

  const user = useUserState();

  // -------------------------------------------------------------------------
  // Append a completed scan to the log
  // -------------------------------------------------------------------------
  const appendLog = useCallback(
    (entry: Omit<ScanLogEntry, 'id'>) => {
      scanCounter.current += 1;
      setScanLog((prev) => [
        { ...entry, id: String(scanCounter.current) },
        ...prev // newest at top
      ]);
    },
    []
  );

  // -------------------------------------------------------------------------
  // Remove a single entry from the log (allow undo of accidental scans)
  // -------------------------------------------------------------------------
  const removeLogEntry = useCallback((id: string) => {
    setScanLog((prev) => prev.filter((e) => e.id !== id));
  }, []);

  // -------------------------------------------------------------------------
  // Default scan handler — navigates to matched model detail page
  // -------------------------------------------------------------------------
  const defaultScan = useCallback(
    (barcode: string, data: any) => {
      let match = false;

      for (const model_type of Object.keys(ModelInformationDict)) {
        if (modelType && model_type !== modelType) {
          continue;
        }

        if (data[model_type]?.['pk']) {
          if (user.hasViewPermission(model_type as ModelType)) {
            const url = getDetailUrl(
              model_type as ModelType,
              data[model_type]['pk']
            );

            if (onScanSuccess) {
              onScanSuccess(barcode, data);
            }

            if (!continuous) {
              onClose();
              navigate(url);
            } else {
              appendLog({
                barcode,
                label:
                  data[model_type]?.['name'] ??
                  data[model_type]?.['reference'] ??
                  `${model_type} #${data[model_type]['pk']}`,
                success: true,
                message: t`Matched`
              });
            }

            match = true;
            break;
          }
        }
      }

      if (!match) {
        const message = t`No matching item found`;
        setError(message);

        if (continuous) {
          appendLog({ barcode, label: barcode, success: false, message });
        }
      }
    },
    [navigate, onClose, user, modelType, continuous, onScanSuccess, appendLog]
  );

  // -------------------------------------------------------------------------
  // Main scan handler
  // -------------------------------------------------------------------------
  const onScan = useCallback(
    (barcode: string) => {
      if (!barcode || barcode.length === 0) {
        return;
      }

      setProcessing(true);
      setError('');

      api
        .post(apiUrl(ApiEndpoints.barcode), { barcode })
        .then((response: any) => {
          const data = response.data ?? {};

          if (callback && data.success && response.status === 200) {
            // Caller-provided callback
            if (modelType) {
              const pk: number = data[modelType]?.['pk'];
              if (!pk) {
                const msg = t`Barcode does not match the expected model type`;
                setError(msg);
                if (continuous) {
                  appendLog({
                    barcode,
                    label: barcode,
                    success: false,
                    message: msg
                  });
                }
                return;
              }
            }

            callback(barcode, data)
              .then((result: BarcodeScanResult) => {
                if (result.success) {
                  hideNotification('barcode-scan');

                  if (!continuous) {
                    // Classic single-scan behaviour: show toast and close
                    showNotification({
                      id: 'barcode-scan',
                      title: t`Success`,
                      message: result.success,
                      color: 'green'
                    });
                    onClose();
                  } else {
                    // Continuous mode: log the scan, stay open, ready for next
                    const label =
                      data[modelType ?? '']?.['name'] ??
                      data[modelType ?? '']?.['reference'] ??
                      barcode;

                    appendLog({
                      barcode,
                      label,
                      success: true,
                      message: result.success
                    });
                  }
                } else {
                  const msg = result.error ?? t`Failed to handle barcode`;
                  setError(msg);
                  if (continuous) {
                    appendLog({
                      barcode,
                      label: barcode,
                      success: false,
                      message: msg
                    });
                  }
                }
              })
              .finally(() => {
                setProcessing(false);
              });
          } else {
            defaultScan(barcode, data);
            setProcessing(false);
          }
        })
        .catch((error) => {
          const _error = extractErrorMessage({
            error,
            field: 'error',
            defaultMessage: t`Failed to scan barcode`
          });

          setError(_error);

          if (continuous) {
            appendLog({
              barcode,
              label: barcode,
              success: false,
              message: _error
            });
          }
        })
        .finally(() => {
          setProcessing(false);
        });
    },
    [callback, defaultScan, modelType, onClose, continuous, appendLog]
  );

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  return (
    <Stack gap='sm'>
      {/* Continuous mode toggle — always visible so user can switch on/off */}
      <Group justify='space-between' align='center'>
        <Checkbox
          label={t`Stay open for multiple scans`}
          checked={continuous}
          onChange={(e) => setContinuous(e.currentTarget.checked)}
          size='sm'
          aria-label='continuous-scan-toggle'
        />
        {continuous && scanLog.length > 0 && (
          <Badge color='blue' variant='light'>
            {scanLog.filter((e) => e.success).length} /{' '}
            {scanLog.length} {t`scanned`}
          </Badge>
        )}
      </Group>

      <BarcodeInput onScan={onScan} error={error} processing={processing} />

      {/* Scan log — only shown in continuous mode */}
      {continuous && scanLog.length > 0 && (
        <>
          <Divider
            label={t`Scan log (newest first)`}
            labelPosition='center'
          />
          <ScrollArea h={200} offsetScrollbars>
            <Timeline active={-1} bulletSize={22} lineWidth={2}>
              {scanLog.map((entry) => (
                <Timeline.Item
                  key={entry.id}
                  bullet={
                    <ThemeIcon
                      size={22}
                      variant='filled'
                      color={entry.success ? 'green' : 'red'}
                      radius='xl'
                    >
                      {entry.success ? (
                        <IconCheck size={14} />
                      ) : (
                        <IconX size={14} />
                      )}
                    </ThemeIcon>
                  }
                  title={
                    <Group gap={6} align='center'>
                      <Text size='sm' fw={500}>
                        {entry.label}
                      </Text>
                      <Tooltip label={t`Remove from log`}>
                        <ActionIcon
                          size='xs'
                          variant='subtle'
                          color='gray'
                          onClick={() => removeLogEntry(entry.id)}
                          aria-label={`remove-scan-${entry.id}`}
                        >
                          <IconCircleX size={12} />
                        </ActionIcon>
                      </Tooltip>
                    </Group>
                  }
                >
                  <Text size='xs' c='dimmed'>
                    {entry.message}
                  </Text>
                  <Text size='xs' c='dimmed' ff='monospace'>
                    {entry.barcode}
                  </Text>
                </Timeline.Item>
              ))}
            </Timeline>
          </ScrollArea>

          <Group justify='space-between'>
            <Button
              variant='subtle'
              size='xs'
              color='red'
              leftSection={<IconTrash size={14} />}
              onClick={() => setScanLog([])}
            >
              {t`Clear log`}
            </Button>
            <Button variant='filled' size='sm' onClick={onClose}>
              {t`Done`} ({scanLog.filter((e) => e.success).length}{' '}
              {t`items`})
            </Button>
          </Group>
        </>
      )}

      {/* Show Done button even when log is empty so user can dismiss */}
      {continuous && scanLog.length === 0 && (
        <Group justify='flex-end'>
          <Button variant='filled' size='sm' onClick={onClose}>
            {t`Done`}
          </Button>
        </Group>
      )}
    </Stack>
  );
}

// --------------------------------------------------------------------------
// useBarcodeScanDialog — convenience hook
// --------------------------------------------------------------------------
export function useBarcodeScanDialog({
  title,
  callback,
  modelType,
  continuous = false
}: Readonly<{
  title: string;
  modelType?: ModelType;
  callback: BarcodeScanCallback;
  /** Set to true to enable multi-scan mode by default */
  continuous?: boolean;
}>) {
  const [opened, setOpened] = useState(false);

  const open = useCallback(() => {
    setOpened(true);
  }, []);

  const dialog = (
    <BarcodeScanDialog
      title={title}
      opened={opened}
      callback={callback}
      modelType={modelType}
      continuous={continuous}
      onClose={() => setOpened(false)}
    />
  );

  return { open, dialog };
}
