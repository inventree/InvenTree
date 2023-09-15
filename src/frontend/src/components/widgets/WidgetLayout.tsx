import { Trans } from '@lingui/macro';
import {
  ActionIcon,
  Container,
  Group,
  Indicator,
  createStyles
} from '@mantine/core';
import { Menu, Text } from '@mantine/core';
import { useDisclosure, useHotkeys } from '@mantine/hooks';
import {
  IconArrowBackUpDouble,
  IconDotsVertical,
  IconLayout2,
  IconSquare,
  IconSquareCheck
} from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';

const ReactGridLayout = WidthProvider(Responsive);

interface LayoutStorage {
  [key: string]: {};
}

const compactType = 'vertical';

const useItemStyle = createStyles((theme) => ({
  backgroundItem: {
    backgroundColor:
      theme.colorScheme === 'dark' ? theme.colors.dark[5] : theme.white,
    maxWidth: '100%',
    padding: '8px',
    boxShadow: theme.shadows.md
  },

  baseItem: {
    maxWidth: '100%',
    padding: '8px'
  }
}));

export interface LayoutItemType {
  i: number;
  val: string | JSX.Element | JSX.Element[] | (() => JSX.Element);
  w?: number;
  h?: number;
  x?: number;
  y?: number;
  minH?: number;
}

export function WidgetLayout({
  items = [],
  className = 'layout',
  localstorageName = 'argl',
  rowHeight = 30
}: {
  items: LayoutItemType[];
  className?: string;
  localstorageName?: string;
  rowHeight?: number;
}) {
  const [layouts, setLayouts] = useState({});
  const [editable, setEditable] = useDisclosure(false);
  const [boxShown, setBoxShown] = useDisclosure(true);
  const { classes } = useItemStyle();

  useEffect(() => {
    let layout = getFromLS('layouts') || [];
    const new_layout = JSON.parse(JSON.stringify(layout));
    setLayouts(new_layout);
  }, []);

  function getFromLS(key: string) {
    let ls: LayoutStorage = {};
    if (localStorage) {
      try {
        ls = JSON.parse(localStorage.getItem(localstorageName) || '') || {};
      } catch (e) {
        /*Ignore*/
      }
    }
    return ls[key];
  }

  function saveToLS(key: string, value: any) {
    if (localStorage) {
      localStorage.setItem(
        localstorageName,
        JSON.stringify({
          [key]: value
        })
      );
    }
  }

  function resetLayout() {
    setLayouts({});
  }

  function onLayoutChange(layout: any, layouts: any) {
    saveToLS('layouts', layouts);
    setLayouts(layouts);
  }

  return (
    <div>
      <WidgetControlBar
        editable={editable}
        editFnc={setEditable.toggle}
        resetLayout={resetLayout}
        boxShown={boxShown}
        boxFnc={setBoxShown.toggle}
      />
      {layouts ? (
        <ReactGridLayout
          className={className}
          cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
          rowHeight={rowHeight}
          layouts={layouts}
          onLayoutChange={(layout, layouts) => onLayoutChange(layout, layouts)}
          compactType={compactType}
          isDraggable={editable}
          isResizable={editable}
        >
          {items.map((item) => {
            return LayoutItem(item, boxShown, classes);
          })}
        </ReactGridLayout>
      ) : (
        <div>
          <Trans>Loading</Trans>
        </div>
      )}
    </div>
  );
}

function WidgetControlBar({
  editable,
  editFnc,
  resetLayout,
  boxShown,
  boxFnc
}: {
  editable: boolean;
  editFnc: () => void;
  resetLayout: () => void;
  boxShown: boolean;
  boxFnc: () => void;
}) {
  useHotkeys([['mod+E', () => editFnc()]]);

  return (
    <Group position="right">
      <Menu
        shadow="md"
        width={200}
        openDelay={100}
        closeDelay={400}
        position="bottom-end"
      >
        <Menu.Target>
          <Indicator
            color="red"
            position="bottom-start"
            processing
            disabled={!editable}
          >
            <ActionIcon variant="transparent">
              <IconDotsVertical />
            </ActionIcon>
          </Indicator>
        </Menu.Target>

        <Menu.Dropdown>
          <Menu.Label>
            <Trans>Layout</Trans>
          </Menu.Label>
          <Menu.Item
            icon={<IconArrowBackUpDouble size={14} />}
            onClick={resetLayout}
          >
            <Trans>Reset Layout</Trans>
          </Menu.Item>
          <Menu.Item
            icon={
              <IconLayout2 size={14} color={editable ? 'red' : undefined} />
            }
            onClick={editFnc}
            rightSection={
              <Text size="xs" color="dimmed">
                ⌘E
              </Text>
            }
          >
            {editable ? <Trans>Stop Edit</Trans> : <Trans>Edit Layout</Trans>}
          </Menu.Item>

          <Menu.Divider />

          <Menu.Label>
            <Trans>Appearance</Trans>
          </Menu.Label>
          <Menu.Item
            icon={
              boxShown ? (
                <IconSquareCheck size={14} />
              ) : (
                <IconSquare size={14} />
              )
            }
            onClick={boxFnc}
          >
            <Trans>Show Boxes</Trans>
          </Menu.Item>
        </Menu.Dropdown>
      </Menu>
    </Group>
  );
}

function LayoutItem(
  item: any,
  backgroundColor: boolean,
  classes: { backgroundItem: string; baseItem: string }
) {
  return (
    <Container
      key={item.i}
      data-grid={{
        w: item.w || 3,
        h: item.h || 3,
        x: item.x || 0,
        y: item.y || 0,
        minH: item.minH || undefined,
        minW: item.minW || undefined
      }}
      className={backgroundColor ? classes.backgroundItem : classes.baseItem}
    >
      {item.val}
    </Container>
  );
}
