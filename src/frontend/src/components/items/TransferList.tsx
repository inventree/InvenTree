import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Button,
  Divider,
  Group,
  Paper,
  Stack,
  Text,
  Tooltip
} from '@mantine/core';
import {
  IconChevronLeft,
  IconChevronRight,
  IconCircleCheck,
  IconCircleChevronLeft,
  IconCircleChevronRight
} from '@tabler/icons-react';
import { useCallback, useEffect, useMemo, useState } from 'react';

export interface TransferListItem {
  value: string | number;
  label: string;
  selected?: boolean;
}

function TransferListGroup({
  items,
  itemSelected,
  itemSwitched
}: {
  items: TransferListItem[];
  itemSelected: (item: TransferListItem) => void;
  itemSwitched: (item: TransferListItem) => void;
}) {
  return (
    <Paper
      p='sm'
      withBorder
      style={{ width: '100%', height: '100%', verticalAlign: 'top' }}
    >
      <Stack
        gap='xs'
        justify='flex-start'
        align='stretch'
        style={{ width: '100%' }}
      >
        {items.map((item) => (
          <Text
            p={2}
            key={item.value}
            onClick={() => itemSelected(item)}
            onDoubleClick={() => itemSwitched(item)}
            style={{
              width: '100%',
              cursor: 'pointer',
              backgroundColor: item.selected
                ? 'var(--mantine-primary-color-light)'
                : undefined
            }}
          >
            {item.label || item.value}
          </Text>
        ))}
        {items.length == 0 && <Text size='sm' fs='italic'>{t`No items`}</Text>}
      </Stack>
    </Paper>
  );
}

export function TransferList({
  available,
  selected,
  onSave
}: {
  available: TransferListItem[];
  selected: TransferListItem[];
  onSave?: (selected: TransferListItem[]) => void;
}) {
  const [leftItems, setLeftItems] = useState<TransferListItem[]>([]);
  const [rightItems, setRightItems] = useState<TransferListItem[]>([]);

  useEffect(() => {
    setRightItems(selected);
    setLeftItems(
      available.filter((item) => !selected.some((i) => i.value === item.value))
    );
  }, [available, selected]);

  const leftToggled = useCallback(
    (item: TransferListItem) => {
      setLeftItems((items) =>
        items.map((i) => {
          if (i.value === item.value) {
            return { ...i, selected: !i.selected };
          }
          return i;
        })
      );
    },
    [setLeftItems]
  );

  const rightToggled = useCallback(
    (item: TransferListItem) => {
      setRightItems((items) =>
        items.map((i) => {
          if (i.value === item.value) {
            return { ...i, selected: !i.selected };
          }
          return i;
        })
      );
    },
    [setRightItems]
  );

  const leftSelected: boolean = useMemo(
    () => leftItems.some((i) => i.selected),
    [leftItems]
  );
  const rightSelected: boolean = useMemo(
    () => rightItems.some((i) => i.selected),
    [rightItems]
  );

  const transferLeftToRight = useCallback(
    (transferAll: boolean) => {
      if (transferAll) {
        setRightItems((items) => items.concat(leftItems));
        setLeftItems([]);
      } else {
        setRightItems((items) =>
          items.concat(leftItems.filter((i) => i.selected))
        );
        setLeftItems((items) => items.filter((i) => !i.selected));
      }
    },
    [leftItems, setLeftItems, setRightItems]
  );

  const transferRightToLeft = useCallback(
    (transferAll: boolean) => {
      if (transferAll) {
        setLeftItems((items) => items.concat(rightItems));
        setRightItems([]);
      } else {
        setLeftItems((items) =>
          items.concat(rightItems.filter((i) => i.selected))
        );
        setRightItems((items) => items.filter((i) => !i.selected));
      }
    },
    [rightItems, setLeftItems, setRightItems]
  );

  return (
    <Paper p='sm' withBorder style={{ width: '100%' }}>
      <Stack gap='xs'>
        <Group justify='space-between'>
          <Text>{t`Available`}</Text>
          <Text>{t`Selected`}</Text>
        </Group>

        <Group justify='space-aprt' wrap='nowrap' align='flex-start'>
          <TransferListGroup
            items={leftItems}
            itemSwitched={() => {}}
            itemSelected={leftToggled}
          />

          <Stack gap='xs' flex={1}>
            <ActionIcon
              variant='outline'
              size='md'
              disabled={leftItems.length == 0}
              onClick={() => transferLeftToRight(true)}
            >
              <IconCircleChevronRight />
            </ActionIcon>
            <ActionIcon
              variant='outline'
              size='md'
              disabled={!leftSelected}
              onClick={() => transferLeftToRight(false)}
            >
              <IconChevronRight />
            </ActionIcon>
            <ActionIcon
              variant='outline'
              size='md'
              disabled={!rightSelected}
              onClick={() => transferRightToLeft(false)}
            >
              <IconChevronLeft />
            </ActionIcon>
            <ActionIcon
              variant='outline'
              size='md'
              disabled={rightItems.length == 0}
              onClick={() => transferRightToLeft(true)}
            >
              <IconCircleChevronLeft />
            </ActionIcon>
          </Stack>

          <TransferListGroup
            items={rightItems}
            itemSelected={rightToggled}
            itemSwitched={() => {}}
          />
        </Group>
        <Divider />
        <Group justify='right' gap='xs'>
          <Tooltip label={t`Save`}>
            <Button
              color='green'
              onClick={() => {
                onSave?.(rightItems);
              }}
              leftSection={<IconCircleCheck />}
            >
              {t`Save`}
            </Button>
          </Tooltip>
        </Group>
      </Stack>
    </Paper>
  );
}
