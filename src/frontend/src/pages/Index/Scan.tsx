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
  IconAlertCircle,
  IconArrowsMaximize,
  IconArrowsMinimize,
  IconLink,
  IconNumber,
  IconPlayerPlayFilled,
  IconPlayerStopFilled,
  IconPlus,
  IconQuestionMark,
  IconSearch,
  IconTrash
} from '@tabler/icons-react';
import { IconX } from '@tabler/icons-react';
import { Html5Qrcode } from 'html5-qrcode';
import { CameraDevice } from 'html5-qrcode/camera/core';
import { useEffect, useState } from 'react';

import { api } from '../../App';
import { DocInfo } from '../../components/items/DocInfo';
import { StylishText } from '../../components/items/StylishText';
import { TitleWithDoc } from '../../components/items/TitleWithDoc';
import { RenderInstance } from '../../components/render/Instance';
import { ModelInformationDict } from '../../components/render/ModelType';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { notYetImplemented } from '../../functions/notifications';
import { IS_DEV_OR_DEMO } from '../../main';
import { apiUrl } from '../../states/ApiState';

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

/*
 * Match the scanned object to a known internal model type
 */
function matchObject(rd: any): [ModelType | undefined, string | undefined] {
  if (rd?.part) {
    return [ModelType.part, rd?.part.pk];
  } else if (rd?.stockitem) {
    return [ModelType.stockitem, rd?.stockitem.pk];
  } else if (rd?.stocklocation) {
    return [ModelType.stocklocation, rd?.stocklocation.pk];
  } else if (rd?.supplierpart) {
    return [ModelType.supplierpart, rd?.supplierpart.pk];
  } else if (rd?.purchaseorder) {
    return [ModelType.purchaseorder, rd?.purchaseorder.pk];
  } else if (rd?.salesorder) {
    return [ModelType.salesorder, rd?.salesorder.pk];
  } else if (rd?.build) {
    return [ModelType.build, rd?.build.pk];
  } else {
    return [undefined, undefined];
  }
}

export default function Scan() {
  const { toggle: toggleFullscreen, fullscreen } = useFullscreen();
  const [history, historyHandlers] = useListState<ScanItem>([]);
  const [historyStorage, setHistoryStorage] = useLocalStorage<ScanItem[]>({
    key: 'scan-history',
    defaultValue: []
  });
  const [selection, setSelection] = useState<string[]>([]);
  const [inputValue, setInputValue] = useLocalStorage<string | null>({
    key: 'input-selection',
    defaultValue: null
  });

  // button handlers
  function btnRunSelectedBarcode() {
    const item = getSelectedItem(selection[0]);
    if (!item) return;
    runBarcode(item?.ref, item?.id);
  }

  const selectionLinked =
    selection.length === 1 && getSelectedItem(selection[0])?.link != undefined;

  function btnOpenSelectedLink() {
    const item = getSelectedItem(selection[0]);
    if (!item) return;
    if (!selectionLinked) return;
    window.open(item.link, '_blank');
  }

  function btnDeleteFullHistory() {
    historyHandlers.setState([]);
    setHistoryStorage([]);
    setSelection([]);
  }

  function btnDeleteHistory() {
    historyHandlers.setState(
      history.filter((item) => !selection.includes(item.id))
    );
    setSelection([]);
  }

  // general functions
  function getSelectedItem(ref: string): ScanItem | undefined {
    if (selection.length === 0) return;
    const item = history.find((item) => item.id === ref);
    if (item?.ref === undefined) return;
    return item;
  }

  function runBarcode(value: string, id?: string) {
    api
      .post(apiUrl(ApiEndpoints.barcode), { barcode: value })
      .then((response) => {
        // update item in history
        if (!id) return;
        const item = getSelectedItem(selection[0]);
        if (!item) return;

        // set link data
        item.link = response.data?.url;

        const rsp = matchObject(response.data);
        item.model = rsp[0];
        item.pk = rsp[1];

        // Fetch instance data
        if (item.model && item.pk) {
          let model_info = ModelInformationDict[item.model];

          if (model_info && model_info.api_endpoint) {
            let url = apiUrl(model_info.api_endpoint, item.pk);

            api
              .get(url)
              .then((response) => {
                item.instance = response.data;
              })
              .catch((err) => {
                console.error('error while fetching instance data at', url);
                console.info(err);
              });
          }
        }

        historyHandlers.setState(history);
      })
      .catch((err) => {
        // 400 and no plugin means no match
        if (
          err.response?.status === 400 &&
          err.response?.data?.plugin === 'None'
        )
          return;
        // otherwise log error
        console.log('error while running barcode', err);
      });
  }

  function addItems(items: ScanItem[]) {
    for (const item of items) {
      historyHandlers.append(item);
      runBarcode(item.ref, item.id);
    }
    setSelection(items.map((item) => item.id));
  }

  // save history data to session storage
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
    switch (inputValue) {
      case InputMethod.Manual:
        return <InputManual action={addItems} />;
      case InputMethod.ImageBarcode:
        return <InputImageBarcode action={addItems} />;
      default:
        return <Text>No input selected</Text>;
    }
  })();

  // selected actions component
  const SelectedActions = () => {
    const uniqueObjectTypes = [
      ...new Set(
        selection
          .map((id) => {
            return history.find((item) => item.id === id)?.model;
          })
          .filter((item) => item != undefined)
      )
    ];

    if (uniqueObjectTypes.length === 0) {
      return (
        <Group spacing={0}>
          <IconQuestionMark color="orange" />
          <Trans>Selected elements are not known</Trans>
        </Group>
      );
    } else if (uniqueObjectTypes.length > 1) {
      return (
        <Group spacing={0}>
          <IconAlertCircle color="orange" />
          <Trans>Multiple object types selected</Trans>
        </Group>
      );
    }
    return (
      <>
        <Text fz="sm" c="dimmed">
          <Trans>Actions for {uniqueObjectTypes[0]} </Trans>
        </Text>
        <Group>
          <ActionIcon onClick={notYetImplemented} title={t`Count`}>
            <IconNumber />
          </ActionIcon>
        </Group>
      </>
    );
  };

  // rendering
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
            <Stack spacing="xs">
              <Group position="apart">
                <TitleWithDoc
                  order={3}
                  text={t`Select the input method you want to use to scan items.`}
                >
                  <Trans>Input</Trans>
                </TitleWithDoc>
                <Select
                  value={inputValue}
                  onChange={setInputValue}
                  data={inputOptions}
                  searchable
                  placeholder={t`Select input method`}
                  nothingFound={t`Nothing found`}
                />
              </Group>
              {inp}
            </Stack>
            <Stack spacing={0}>
              <TitleWithDoc
                order={3}
                text={t`Depending on the selected parts actions will be shown here. Not all barcode types are supported currently.`}
              >
                <Trans>Action</Trans>
              </TitleWithDoc>
              {selection.length === 0 ? (
                <Text>
                  <Trans>No selection</Trans>
                </Text>
              ) : (
                <>
                  <Text>
                    <Trans>{selection.length} items selected</Trans>
                  </Text>
                  <Text fz="sm" c="dimmed">
                    <Trans>General Actions</Trans>
                  </Text>
                  <Group>
                    <ActionIcon
                      color="red"
                      onClick={btnDeleteHistory}
                      title={t`Delete`}
                    >
                      <IconTrash />
                    </ActionIcon>
                    <ActionIcon
                      onClick={btnRunSelectedBarcode}
                      disabled={selection.length > 1}
                      title={t`Lookup part`}
                    >
                      <IconSearch />
                    </ActionIcon>
                    <ActionIcon
                      onClick={btnOpenSelectedLink}
                      disabled={!selectionLinked}
                      title={t`Open Link`}
                    >
                      <IconLink />
                    </ActionIcon>
                  </Group>
                  <SelectedActions />
                </>
              )}
            </Stack>
          </Stack>
        </Col>
        <Col span={8}>
          <Group position="apart">
            <TitleWithDoc
              order={3}
              text={t`History is locally kept in this browser.`}
              detail={t`The history is kept in this browser's local storage. So it won't be shared with other users or other devices but is persistent through reloads. You can select items in the history to perform actions on them. To add items, scan/enter them in the Input area.`}
            >
              <Trans>History</Trans>
            </TitleWithDoc>
            <ActionIcon color="red" onClick={btnDeleteFullHistory}>
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
        <td>
          {item.pk && item.model && item.instance ? (
            <RenderInstance model={item.model} instance={item.instance} />
          ) : (
            item.ref
          )}
        </td>
        <td>{item.model}</td>
        <td>{item.source}</td>
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
              <Trans>Item</Trans>
            </th>
            <th>
              <Trans>Type</Trans>
            </th>
            <th>
              <Trans>Source</Trans>
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

  function btnAddItem() {
    if (value === '') return;

    const new_item: ScanItem = {
      id: randomId(),
      ref: value,
      data: { item: value },
      timestamp: new Date(),
      source: InputMethod.Manual
    };
    action([new_item]);
    setValue('');
  }

  function btnAddDummyItem() {
    const new_item: ScanItem = {
      id: randomId(),
      ref: 'Test item',
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
          onKeyDown={getHotkeyHandler([['Enter', btnAddItem]])}
        />
        <ActionIcon onClick={btnAddItem} w={16}>
          <IconPlus />
        </ActionIcon>
      </Group>

      {IS_DEV_OR_DEMO && (
        <Button onClick={btnAddDummyItem} variant="outline">
          <Trans>Add dummy item</Trans>
        </Button>
      )}
    </>
  );
}

/* Input that uses QR code detection from images */
function InputImageBarcode({ action }: inputProps) {
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
    action([
      {
        id: randomId(),
        ref: decodedText,
        data: decodedText,
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

// endregion
