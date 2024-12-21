import { Trans, t } from '@lingui/macro';
import {
  ActionIcon,
  Button,
  Checkbox,
  Grid,
  Group,
  ScrollArea,
  Space,
  Stack,
  Table,
  Text,
  rem
} from '@mantine/core';
import { useFullscreen, useListState, useLocalStorage } from '@mantine/hooks';
import {
  IconAlertCircle,
  IconArrowsMaximize,
  IconArrowsMinimize,
  IconLink,
  IconNumber,
  IconQuestionMark,
  IconSearch,
  IconTrash
} from '@tabler/icons-react';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { api } from '../../App';
import { BarcodeInput } from '../../components/barcodes/BarcodeInput';
import { DocInfo } from '../../components/items/DocInfo';
import { StylishText } from '../../components/items/StylishText';
import { TitleWithDoc } from '../../components/items/TitleWithDoc';
import PageTitle from '../../components/nav/PageTitle';
import { RenderInstance } from '../../components/render/Instance';
import { ModelInformationDict } from '../../components/render/ModelType';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { notYetImplemented } from '../../functions/notifications';
import { apiUrl } from '../../states/ApiState';

export interface ScanItem {
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
          const model_info = ModelInformationDict[item.model];

          if (model_info?.api_endpoint) {
            const url = apiUrl(model_info.api_endpoint, item.pk);

            api
              .get(url)
              .then((response) => {
                item.instance = response.data;
                const list_idx = history.findIndex((i) => i.id === id);
                historyHandlers.setItem(list_idx, item);
              })
              .catch((err) => {
                console.error('error while fetching instance data at', url);
                console.info(err);
              });
          }
        } else {
          historyHandlers.setState(history);
        }
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

  const scanBarcode = useCallback((barcode: string) => {
    // TODO: Fetch via API
  }, []);

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
        <Group gap={0}>
          <IconQuestionMark color='orange' />
          <Trans>Selected elements are not known</Trans>
        </Group>
      );
    } else if (uniqueObjectTypes.length > 1) {
      return (
        <Group gap={0}>
          <IconAlertCircle color='orange' />
          <Trans>Multiple object types selected</Trans>
        </Group>
      );
    }
    return (
      <>
        <Text fz='sm' c='dimmed'>
          <Trans>Actions for {uniqueObjectTypes[0]} </Trans>
        </Text>
        <Group>
          <ActionIcon
            onClick={notYetImplemented}
            title={t`Count`}
            variant='default'
          >
            <IconNumber />
          </ActionIcon>
        </Group>
      </>
    );
  };

  // rendering
  return (
    <>
      <PageTitle title={t`Barcode Scanning`} />
      <Group justify='space-between'>
        <Group justify='left'>
          <StylishText>
            <Trans>Scan Page</Trans>
          </StylishText>
          <DocInfo
            text={t`This page can be used for continuously scanning items and taking actions on them.`}
          />
        </Group>
        <Button
          onClick={toggleFullscreen}
          size='sm'
          variant='subtle'
          title={t`Toggle Fullscreen`}
        >
          {fullscreen ? <IconArrowsMaximize /> : <IconArrowsMinimize />}
        </Button>
      </Group>
      <Space h={'md'} />
      <Grid maw={'100%'}>
        <Grid.Col span={4}>
          <Stack gap='xs'>
            <BarcodeInput onScan={scanBarcode} />
            <Stack gap={0}>
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
                  <Text fz='sm' c='dimmed'>
                    <Trans>General Actions</Trans>
                  </Text>
                  <Group>
                    <ActionIcon
                      color='red'
                      onClick={btnDeleteHistory}
                      title={t`Delete`}
                      variant='default'
                    >
                      <IconTrash />
                    </ActionIcon>
                    <ActionIcon
                      onClick={btnRunSelectedBarcode}
                      disabled={selection.length > 1}
                      title={t`Lookup part`}
                      variant='default'
                    >
                      <IconSearch />
                    </ActionIcon>
                    <ActionIcon
                      onClick={btnOpenSelectedLink}
                      disabled={!selectionLinked}
                      title={t`Open Link`}
                      variant='default'
                    >
                      <IconLink />
                    </ActionIcon>
                  </Group>
                  <SelectedActions />
                </>
              )}
            </Stack>
          </Stack>
        </Grid.Col>
        <Grid.Col span={8}>
          <Group justify='space-between'>
            <TitleWithDoc
              order={3}
              text={t`History is locally kept in this browser.`}
              detail={t`The history is kept in this browser's local storage. So it won't be shared with other users or other devices but is persistent through reloads. You can select items in the history to perform actions on them. To add items, scan/enter them in the Input area.`}
            >
              <Trans>History</Trans>
            </TitleWithDoc>
            <ActionIcon
              color='red'
              onClick={btnDeleteFullHistory}
              variant='default'
              title={t`Delete History`}
            >
              <IconTrash />
            </ActionIcon>
          </Group>
          <HistoryTable
            data={history}
            selection={selection}
            setSelection={setSelection}
          />
        </Grid.Col>
      </Grid>
    </>
  );
}

function HistoryTable({
  data,
  selection,
  setSelection
}: Readonly<{
  data: ScanItem[];
  selection: string[];
  setSelection: React.Dispatch<React.SetStateAction<string[]>>;
}>) {
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

  const rows = useMemo(() => {
    return data.map((item) => {
      return (
        <tr key={item.id}>
          <td>
            <Checkbox
              checked={selection.includes(item.id)}
              onChange={() => toggleRow(item.id)}
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
  }, [data, selection]);

  // rendering
  if (data.length === 0)
    return (
      <Text>
        <Trans>No history</Trans>
      </Text>
    );
  return (
    <ScrollArea>
      <Table miw={800} verticalSpacing='sm'>
        <thead>
          <tr>
            <th style={{ width: rem(40) }}>
              <Checkbox
                onChange={toggleAll}
                checked={selection.length === data.length}
                indeterminate={
                  selection.length > 0 && selection.length !== data.length
                }
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
