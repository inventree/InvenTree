import { Trans, t } from '@lingui/macro';
import {
  ActionIcon,
  Button,
  Checkbox,
  Col,
  Grid,
  Group,
  ScrollArea,
  Select,
  Space,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
  rem
} from '@mantine/core';
import { Badge, Container } from '@mantine/core';
import {
  getHotkeyHandler,
  randomId,
  useFullscreen,
  useListState,
  useLocalStorage
} from '@mantine/hooks';
import { useDocumentVisibility } from '@mantine/hooks';
import { showNotification } from '@mantine/notifications';
import {
  IconArrowsMaximize,
  IconArrowsMinimize,
  IconPlus,
  IconTrash
} from '@tabler/icons-react';
import { IconX } from '@tabler/icons-react';
import { Html5Qrcode } from 'html5-qrcode';
import { CameraDevice } from 'html5-qrcode/camera/core';
import { Html5QrcodeResult } from 'html5-qrcode/core';
import { useEffect, useState } from 'react';

import { api } from '../../App';
import { DocInfo } from '../../components/items/DocInfo';
import { StylishText } from '../../components/items/StylishText';
import { IS_DEV_OR_DEMO } from '../../main';

interface ScanItem {
  id: string;
  name: string;
  data: any;
  timestamp: Date;
  source: string;
}

export default function Scan() {
  const { toggle: toggleFullscreen, fullscreen } = useFullscreen();
  const [history, historyHandlers] = useListState<ScanItem>([]);
  const [historyStorage, setHistoryStorage] = useLocalStorage<ScanItem[]>({
    key: 'scan-history',
    defaultValue: []
  });
  const [selection, setSelection] = useState<string[]>([]);
  const [value, setValue] = useState<string | null>(null);

  function runBarcode(value: string) {
    api.post('/barcode/', { barcode: value }).then((response) => {
      showNotification({
        title: response.data?.success || t`Unknown response`,
        message: JSON.stringify(response.data),
        color: response.data?.success ? 'teal' : 'red'
      });
      if (response.data?.url) {
        showNotification({
          title: t`Opening URL`,
          message: response.data.url,
          color: 'teal'
        });
        // window.location.href = response.data.url;
      }
    });
  }

  function runSelectedBarcode() {
    if (selection.length === 0) return;
    // get item from history by selection id
    const item = history.find((item) => item.id === selection[0]);
    console.log(item);
    runBarcode(item?.name);
  }

  function addItems(items: ScanItem[]) {
    for (const item of items) {
      historyHandlers.append(item);
      runBarcode(item.name);
    }
    setSelection(items.map((item) => item.id));
  }

  function deleteFullHistory() {
    historyHandlers.setState([]);
    setHistoryStorage([]);
    setSelection([]);
  }

  function deleteHistory() {
    historyHandlers.setState(
      history.filter((item) => !selection.includes(item.id))
    );
    setSelection([]);
  }

  // save data to session storage
  useEffect(() => {
    if (history.length === 0) return;
    setHistoryStorage(history);
  }, [history]);

  // load data from session storage on mount
  if (history.length === 0 && historyStorage.length != 0) {
    historyHandlers.setState(historyStorage);
  }

  // input stuff
  const inputOptions = [
    { value: InputMethod.Manual, label: t`Manual input` },
    { value: InputMethod.ImageBarcode, label: t`Image Barcode` }
  ];

  const inp = (function () {
    switch (value) {
      case InputMethod.Manual:
        return <InputManual action={addItems} />;
      case InputMethod.ImageBarcode:
        return <InputImageBarcode action={addItems} />;
      default:
        return <Text>No input selected</Text>;
    }
  })();

  return (
    <>
      <Group position="apart">
        <Group position="left">
          <StylishText>
            <Trans>Scan Page</Trans>
          </StylishText>
          <DocInfo
            text={t`This page can be used for continuously scanning items and taking actions on them.`}
          />
        </Group>
        <Button onClick={toggleFullscreen} size="sm" variant="subtle">
          {fullscreen ? <IconArrowsMaximize /> : <IconArrowsMinimize />}
        </Button>
      </Group>
      <Space h={'md'} />
      <Grid maw={'100%'}>
        <Col span={4}>
          <Stack>
            <Stack>
              <Group>
                <Title order={3}>
                  <Trans>Input</Trans>
                </Title>
                <DocInfo
                  text={t`Select the input method you want to use to scan items.`}
                />
              </Group>
              <Select
                value={value}
                onChange={setValue}
                data={inputOptions}
                searchable
                placeholder={t`Select input method`}
                nothingFound={t`Nothing found`}
              />
              {inp}
            </Stack>
            <Stack>
              <Title order={3}>
                <Trans>Action</Trans>
              </Title>
              {selection.length === 0 ? (
                <Text>
                  <Trans>No selection</Trans>
                </Text>
              ) : (
                <>
                  <Text>
                    <Trans>{selection.length} items selected</Trans>
                  </Text>
                  <Group>
                    <ActionIcon color="red" onClick={deleteHistory}>
                      <IconTrash />
                    </ActionIcon>
                    <Button onClick={runSelectedBarcode}>
                      <Trans>Run Barcode</Trans>
                    </Button>
                  </Group>
                </>
              )}
            </Stack>
          </Stack>
        </Col>
        <Col span={8}>
          <Group position="apart">
            <Group>
              <Title order={3}>
                <Trans>History</Trans>
              </Title>
              <DocInfo
                text={t`History is locally kept in this browser.`}
                detail={t`The history is kept in this browser's local storage. So it won't be shared with other users or other devices but is persistent through reloads. You can select items in the history to perform actions on them. To add items, scan/enter them in the Input area.`}
              />
            </Group>

            <ActionIcon color="red" onClick={deleteFullHistory}>
              <IconTrash />
            </ActionIcon>
          </Group>
          <HistoryTable
            data={history}
            selection={selection}
            setSelection={setSelection}
          />
        </Col>
      </Grid>
    </>
  );
}

function HistoryTable({
  data,
  selection,
  setSelection
}: {
  data: ScanItem[];
  selection: string[];
  setSelection: React.Dispatch<React.SetStateAction<string[]>>;
}) {
  const toggleRow = (id: string) =>
    setSelection((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id]
    );
  const toggleAll = () =>
    setSelection((current) =>
      current.length === data.length ? [] : data.map((item) => item.id)
    );

  const rows = data.map((item) => {
    const selected = selection.includes(item.id);
    return (
      <tr key={item.id}>
        <td>
          <Checkbox
            checked={selection.includes(item.id)}
            onChange={() => toggleRow(item.id)}
            transitionDuration={0}
          />
        </td>
        <td>{item.id}</td>
        <td>{item.name}</td>
        <td>{item.timestamp?.toString()}</td>
      </tr>
    );
  });

  // rendering
  if (data.length === 0)
    return (
      <Text>
        <Trans>No history</Trans>
      </Text>
    );
  return (
    <ScrollArea>
      <Table miw={800} verticalSpacing="sm">
        <thead>
          <tr>
            <th style={{ width: rem(40) }}>
              <Checkbox
                onChange={toggleAll}
                checked={selection.length === data.length}
                indeterminate={
                  selection.length > 0 && selection.length !== data.length
                }
                transitionDuration={0}
              />
            </th>
            <th>
              <Trans>Id</Trans>
            </th>
            <th>
              <Trans>Name</Trans>
            </th>
            <th>
              <Trans>Scanned at</Trans>
            </th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </Table>
    </ScrollArea>
  );
}

// region input stuff
enum InputMethod {
  Manual = 'manually',
  ImageBarcode = 'imageBarcode'
}

interface inputProps {
  action: (items: ScanItem[]) => void;
}

function InputManual({ action }: inputProps) {
  const [value, setValue] = useState<string>('');

  function addItem() {
    if (value === '') return;

    const new_item: ScanItem = {
      id: randomId(),
      name: value,
      data: { item: value },
      timestamp: new Date(),
      source: InputMethod.Manual
    };
    action([new_item]);
    setValue('');
  }

  function addDummyItem() {
    const new_item: ScanItem = {
      id: randomId(),
      name: 'Test item',
      data: {},
      timestamp: new Date(),
      source: InputMethod.Manual
    };
    action([new_item]);
  }

  return (
    <>
      <Group>
        <TextInput
          placeholder={t`Enter item serial or data`}
          value={value}
          onChange={(event) => setValue(event.currentTarget.value)}
          onKeyDown={getHotkeyHandler([['Enter', addItem]])}
        />
        <ActionIcon onClick={addItem} w={16}>
          <IconPlus />
        </ActionIcon>
      </Group>

      {IS_DEV_OR_DEMO && (
        <Button onClick={addDummyItem} variant="outline">
          <Trans>Add dummy item</Trans>
        </Button>
      )}
    </>
  );
}

/* Input that uses QR code detection from images */
function InputImageBarcode({ action }: inputProps) {
  // TODO: implement this @matmair

  const [qrCodeScanner, setQrCodeScanner] = useState<Html5Qrcode | null>(null);
  const [camId, setCamId] = useLocalStorage<CameraDevice | null>({
    key: 'camId',
    defaultValue: null
  });
  const [ScanningEnabled, setIsScanning] = useState<boolean>(false);
  const [wasAutoPaused, setWasAutoPaused] = useState<boolean>(false);
  const documentState = useDocumentVisibility();

  let lastValue: string = '';

  // Mount QR code once we are loaded
  useEffect(() => {
    setQrCodeScanner(new Html5Qrcode('reader'));
  }, []);

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
  function onScanSuccess(
    decodedText: string,
    decodedResult: Html5QrcodeResult
  ) {
    qrCodeScanner?.pause();

    // dedouplication
    if (decodedText === lastValue) {
      qrCodeScanner?.resume();
      return;
    }
    lastValue = decodedText;

    // submit value upstream
    action([
      {
        id: randomId(),
        name: decodedText,
        data: decodedResult,
        timestamp: new Date(),
        source: InputMethod.ImageBarcode
      }
    ]);
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
        </>
      )}
    </Stack>
  );
}

// endregion
