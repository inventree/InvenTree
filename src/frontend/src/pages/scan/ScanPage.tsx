import { Trans, t } from '@lingui/macro';
import {
  ActionIcon,
  Button,
  Col,
  Grid,
  Group,
  Select,
  Space,
  Stack,
  Text
} from '@mantine/core';
import { useFullscreen, useListState, useLocalStorage } from '@mantine/hooks';
import {
  IconAlertCircle,
  IconArrowsMaximize,
  IconArrowsMinimize,
  IconLink,
  IconNumber,
  IconQuestionMark,
  IconTrash
} from '@tabler/icons-react';
import { AxiosResponse } from 'axios';
import { useEffect, useState } from 'react';

import { api } from '../../App';
import { DocInfo } from '../../components/items/DocInfo';
import { StylishText } from '../../components/items/StylishText';
import { TitleWithDoc } from '../../components/items/TitleWithDoc';
import { ModelInformationDict } from '../../components/render/ModelType';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { notYetImplemented } from '../../functions/notifications';
import { apiUrl } from '../../states/ApiState';
import BarcodeInputImage from './BarcodeInputImage';
import BarcodeInputManual from './BarcodeInputManual';
import ScanCart from './ScanCart';
import HistoryTable from './ScanHistoryTable';

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
const matchObject = (rd: any): [ModelType | undefined, string | undefined] => {
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
};

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

  // State
  const barcodeState = {
    validating: false,
    valid: false,
    loading: false,
    loaded: false
  };

  let scannedItems: ScanItem[] = [];

  const createScanItem = () => {};

  const validateBarcode = async (
    barcodeValue: string
  ): Promise<false | AxiosResponse> => {
    try {
      let response = await api.post(apiUrl(ApiEndpoints.barcode), {
        barcode: barcodeValue
      });

      // Return barcode validation data
      return response.data;
    } catch (error) {
      console.log(
        `Error validating barcode: '${barcodeValue}'\nError: `,
        error
      );
      return false;
    }
  };

  const loadBarcode = async (barcodeURL: string) => {
    try {
      let response = await api.get(barcodeURL);
      return response.data;
    } catch (error) {
      console.log(
        `Error loading barcode data from: '${barcodeURL}'\nError: `,
        error
      );
      return false;
    }
  };

  const addItem = async (item: ScanItem) => {
    // Validate Barcode
    const result = await validateBarcode(item.ref);
    if (!result) return;

    // Match barcode to inventree item object
    const processedItem = matchObject(result);
    if (!processedItem[0]) return;

    // Update item properties
    item.model = processedItem[0];
    item.pk = processedItem[1];

    // Extract API link
    let modelInfo = ModelInformationDict[processedItem[0]];
    const url = apiUrl(modelInfo.api_endpoint, processedItem[1]);
    const barcodeResult = await loadBarcode(url);

    // Set item instance to API result
    item.instance = barcodeResult;

    scannedItems.push(item);
    historyHandlers.append(item);
  };

  // save history data to session storage
  useEffect(() => {
    if (history.length === 0) return;
    setHistoryStorage(history);
  }, [history]);

  // load data from session storage on mount
  if (history.length === 0 && historyStorage.length != 0) {
    historyHandlers.setState(historyStorage);
  }

  // region input stuff
  enum InputMethod {
    Manual = 'manually',
    ImageBarcode = 'imageBarcode'
  }

  // input stuff
  const inputOptions = [
    { value: InputMethod.Manual, label: t`Manual input` },
    { value: InputMethod.ImageBarcode, label: t`Image Barcode` }
  ];

  const barcodeInputMethod = (() => {
    switch (inputValue) {
      case InputMethod.Manual:
        return <BarcodeInputManual action={addItem} />;
      case InputMethod.ImageBarcode:
        return <BarcodeInputImage action={addItem} />;
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
      {/* Page Header */}
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

      {/* Page Content */}
      <Grid maw={'100%'}>
        {/* Left Column */}
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
              {barcodeInputMethod}
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

        {/* Main Content */}
        <Col span={8}>
          {/* Scan Cart Component */}
          <ScanCart items={history} />

          <Space h={'md'} />

          {/* History Table Title */}
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
