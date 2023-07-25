import { Trans } from '@lingui/macro';
import { Button, Container, Group, createStyles } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconCheck, IconEdit, IconPlus } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { lazy } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

import { LoadingItem } from '../../functions/loading';

const ReactGridLayout = WidthProvider(Responsive);

const vals = [
  {
    i: 1,
    val: (
      <LoadingItem
        item={lazy(() => import('../../components/widgets/GetStartedWidget'))}
      />
    ),
    w: 12,
    h: 7,
    x: 0,
    y: 0,
    minH: 7
  },
  {
    i: 2,
    val: (
      <LoadingItem
        item={lazy(() => import('../../components/widgets/DisplayWidget'))}
      />
    ),
    w: 3,
    h: 3,
    x: 0,
    y: 7,
    minH: 3
  },
  {
    i: 3,
    val: (
      <LoadingItem
        item={lazy(() => import('../../components/widgets/SizeDemoWidget'))}
      />
    ),
    w: 3,
    h: 4,
    x: 3,
    y: 7
  },
  {
    i: 4,
    val: (
      <LoadingItem
        item={lazy(() => import('../../components/widgets/FeedbackWidget'))}
      />
    ),
    w: 4,
    h: 6,
    x: 0,
    y: 9
  },
  { i: 5, val: 'E', w: 2, h: 3, x: 6, y: 7 }
];
const compactType = 'vertical';

const useItemStyle = createStyles((theme) => ({
  backgroundItem: {
    backgroundColor:
      theme.colorScheme === 'dark'
        ? theme.colors.gray[9]
        : theme.colors.gray[1],
    maxWidth: '100%',
    padding: '8px'
  },

  baseItem: {
    maxWidth: '100%',
    padding: '8px'
  },

  layoutEditGroup: {
    border: `1px red dashed`,
    borderRadius: '8px',
    backgroundColor:
      theme.colorScheme === 'dark' ? theme.colors.gray[9] : theme.colors.gray[1]
  }
}));

export function LocalStorageLayout({
  className = 'layout',
  localstorageName = 'argl',
  rowHeight = 30
}: {
  className?: string;
  localstorageName?: string;
  rowHeight?: number;
}) {
  const [layouts, setLayouts] = useState({});
  const [editable, setEditable] = useDisclosure(false);
  const [backgroundColor, setBackgroundColor] = useDisclosure(true);
  const { classes } = useItemStyle();

  useEffect(() => {
    let layout = getFromLS('layouts') || [];
    const new_layout = JSON.parse(JSON.stringify(layout));
    setLayouts(new_layout);
  }, []);

  function getFromLS(key: string) {
    let ls = {};
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
      <Group position="left">
        <Group className={editable ? classes.layoutEditGroup : ''}>
          <Button
            leftIcon={editable ? <IconCheck /> : <IconEdit />}
            compact={true}
            onClick={setEditable.toggle}
            variant="outline"
            {...(editable ? { color: 'red' } : {})}
          >
            <Trans>Layout</Trans>
          </Button>
          {editable && (
            <>
              <Button onClick={resetLayout} compact={true} variant="light">
                <Trans>Reset Layout</Trans>
              </Button>
              <Button
                onClick={setBackgroundColor.toggle}
                compact={true}
                variant={backgroundColor ? 'light' : 'outline'}
              >
                <Trans>Background Color</Trans>
              </Button>
            </>
          )}
        </Group>
      </Group>
      <div>
        {layouts ? (
          <ReactGridLayout
            className={className}
            cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
            rowHeight={rowHeight}
            layouts={layouts}
            onLayoutChange={(layout, layouts) =>
              onLayoutChange(layout, layouts)
            }
            compactType={compactType}
            isDraggable={editable}
            isResizable={editable}
          >
            {vals.map(getItems(backgroundColor, classes))}
          </ReactGridLayout>
        ) : (
          <div>
            <Trans>Loading</Trans>
          </div>
        )}
      </div>
    </div>
  );
}

function getItems(
  backgroundColor: boolean,
  classes: { backgroundItem: string; baseItem: string }
) {
  return function (item: any) {
    return LayoutItem(item, backgroundColor, classes);
  };
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
