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
import {
  getHotkeyHandler,
  randomId,
  useFullscreen,
  useListState,
  useLocalStorage
} from '@mantine/hooks';
import {
  IconArrowsMaximize,
  IconArrowsMinimize,
  IconPlus,
  IconTrash
} from '@tabler/icons-react';
import { useEffect, useState } from 'react';

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

  function addItems(items: ScanItem[]) {
    for (const item of items) {
      historyHandlers.append(item);
    }
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
              <Title order={3}>
                <Trans>Input</Trans>
              </Title>
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
                text={t`Histroy is locally kept in this browser.`}
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
    const new_item: ScanItem = {
      id: randomId(),
      name: value,
      data: { item: value },
      timestamp: new Date(),
      source: InputMethod.Manual
    };
    action([new_item]);
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
          Add dummy item
        </Button>
      )}
    </>
  );
}

/* Input that uses QR code detection from images */
function InputImageBarcode({ action }: inputProps) {
  // TODO: implement this @matmair
  return <Text>Image barcode</Text>;
}

// endregion
