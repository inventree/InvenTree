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
import {
  randomId,
  useFullscreen,
  useListState,
  useLocalStorage
} from '@mantine/hooks';
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
import type { ModelType } from '../../enums/ModelType';
import {
  notYetImplemented,
  showApiErrorMessage
} from '../../functions/notifications';
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

export default function Scan() {
  const { toggle: toggleFullscreen, fullscreen } = useFullscreen();
  const [history, historyHandlers] = useListState<ScanItem>([]);
  const [historyStorage, setHistoryStorage] = useLocalStorage<ScanItem[]>({
    key: 'scan-history',
    defaultValue: []
  });
  const [selection, setSelection] = useState<string[]>([]);

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

  // Fetch model instance based on scan item
  const fetchInstance = useCallback(
    (item: ScanItem) => {
      if (!item.model || !item.pk) {
        return;
      }

      const model_info = ModelInformationDict[item.model];

      api
        .get(apiUrl(model_info.api_endpoint, item.pk))
        .then((response) => {
          item.instance = response.data;
          historyHandlers.append(item);
        })
        .catch((error) => {
          showApiErrorMessage({
            error: error,
            title: t`API Error`,
            message: t`Failed to fetch instance data`
          });
        });
    },
    [api]
  );

  const scanBarcode = useCallback(
    (barcode: string) => {
      api
        .post(apiUrl(ApiEndpoints.barcode), { barcode: barcode })
        .then((response) => {
          const data = response?.data ?? {};

          let match = false;

          for (const model_type of Object.keys(ModelInformationDict)) {
            if (data[model_type]?.pk) {
              match = true;
              fetchInstance({
                id: randomId(),
                ref: barcode,
                data: data,
                timestamp: new Date(),
                source: 'scan',
                model: model_type as ModelType,
                pk: data[model_type]?.pk
              });
            }
          }

          // If no match is found, add an empty result
          if (!match) {
            historyHandlers.append({
              id: randomId(),
              ref: barcode,
              data: data,
              timestamp: new Date(),
              source: 'scan'
            });
          }
        })
        .catch((error) => {
          showApiErrorMessage({
            error: error,
            message: t`Failed to scan barcode`,
            title: t`Scan Error`,
            field: 'error'
          });
        });
    },
    [fetchInstance]
  );

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
                      onClick={notYetImplemented}
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
