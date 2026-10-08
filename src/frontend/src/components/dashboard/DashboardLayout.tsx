import { t } from '@lingui/core/macro';
import {
  Alert,
  Button,
  Card,
  Center,
  Divider,
  Loader,
  Space,
  Text,
  useMantineColorScheme
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconExclamationCircle, IconInfoCircle } from '@tabler/icons-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { type Layout, Responsive, WidthProvider } from 'react-grid-layout';

import { useInvenTreeHotkeys } from '@lib/functions/Events';
import { useShallow } from 'zustand/react/shallow';
import { useDashboardItems } from '../../hooks/UseDashboardItems';
import { useLocalState } from '../../states/LocalState';
import { useUserState } from '../../states/UserState';
import DashboardMenu from './DashboardMenu';
import DashboardWidget, { type DashboardWidgetProps } from './DashboardWidget';
import DashboardWidgetDrawer from './DashboardWidgetDrawer';

const ReactGridLayout = WidthProvider(Responsive);

const BREAKPOINT_COLS: Record<string, number> = {
  lg: 12,
  md: 10,
  sm: 6,
  xs: 4,
  xxs: 2
};

const REMOVED_WIDGET_LABELS = new Set([
  'dash-traffic-source',
  'dash-access-logs',
  'dash-profit-cat',
  'dash-order-summary',
  'dash-stock-level',
  'dash-restock'
]);

function getDefaultWidgetWidth(
  widget: DashboardWidgetProps | undefined,
  cols: number
): number {
  const minW = widget?.minWidth ?? 1;
  if (minW >= 8) {
    return cols;
  }
  if (minW >= 4) {
    return Math.min(Math.max(6, minW), cols);
  }
  // Standard metric / stat widgets: 4 per row on 12-col grid
  if (cols >= 12) return 3;
  if (cols === 10) return 5;
  if (cols >= 6) return 3;
  if (cols >= 4) return 2;
  return cols;
}

function getDefaultWidgetHeight(
  widget: DashboardWidgetProps | undefined
): number {
  return Math.max(widget?.minHeight ?? 2, 2);
}

function findNextHorizontalSlot(
  currentLayout: Layout[],
  w: number,
  h: number,
  cols: number
): { x: number; y: number } {
  const collides = (x: number, y: number) => {
    return currentLayout.some((item) => {
      const ix = item.x;
      const iy = item.y;
      const iw = item.w;
      const ih = item.h;
      return !(x + w <= ix || x >= ix + iw || y + h <= iy || y >= iy + ih);
    });
  };

  let y = 0;
  while (y < 200) {
    for (let x = 0; x <= cols - w; x++) {
      if (!collides(x, y)) {
        return { x, y };
      }
    }
    y++;
  }
  return { x: 0, y };
}

function normalizeLayoutHorizontally(
  layout: Layout[],
  widgetsList: DashboardWidgetProps[],
  cols: number
): Layout[] {
  const isStackedBuggy =
    layout.length > 1 &&
    layout.filter((item) => item.x === 0 && (item.w ?? 1) <= 2).length >=
      layout.length - 1;

  // Check if any metric/query widgets have mismatched height (< 2) or mismatched width compared to standard grid defaults
  const hasMismatchedWidgets = layout.some((item) => {
    if (item.i === 'dash-stats' || item.i === 'news' || item.i === 'gstart') {
      return false;
    }
    const widget = widgetsList.find((w) => w.label === item.i);
    const expectedW = getDefaultWidgetWidth(widget, cols);
    const expectedH = getDefaultWidgetHeight(widget);
    return (item.h ?? 1) < expectedH || (item.w ?? 1) !== expectedW;
  });

  // Check if standard widgets have diagonal staircasing or unnecessary vertical gaps
  const isScatteredOrGapped = (() => {
    const standardItems = layout.filter(
      (item) => item.i !== 'dash-stats' && item.i !== 'news' && item.i !== 'gstart'
    );
    if (standardItems.length <= 1) return false;

    const specialItems = layout.filter(
      (item) => item.i === 'dash-stats' || item.i === 'news' || item.i === 'gstart'
    );
    const startY = specialItems.reduce(
      (maxY, item) => Math.max(maxY, (item.y ?? 0) + (item.h ?? 2)),
      0
    );

    const maxItemsPerRow = Math.max(1, Math.floor(cols / 3));
    // If all standard widgets would fit on a single row (<= maxItemsPerRow), but any is placed below startY
    if (
      standardItems.length <= maxItemsPerRow &&
      standardItems.some((item) => (item.y ?? 0) > startY)
    ) {
      return true;
    }

    // Check if any standard widget is on a lower row when preceding rows have empty room
    return standardItems.some((item) => {
      const iy = item.y ?? 0;
      if (iy <= startY) return false;
      const itemsInEarlierRows = standardItems.filter(
        (other) => (other.y ?? 0) < iy
      );
      const widthUsed = itemsInEarlierRows.reduce(
        (sum, other) => sum + (other.w ?? 3),
        0
      );
      const availableWidthBefore = Math.floor((iy - startY) / 2) * cols;
      return widthUsed < availableWidthBefore;
    });
  })();

  if (!isStackedBuggy && !hasMismatchedWidgets && !isScatteredOrGapped) {
    return layout;
  }

  // Sort layout items to preserve reading order: special widgets first, then top-to-bottom, left-to-right
  const sortedLayout = [...layout].sort((a, b) => {
    const isSpecialA =
      a.i === 'dash-stats' || a.i === 'news' || a.i === 'gstart';
    const isSpecialB =
      b.i === 'dash-stats' || b.i === 'news' || b.i === 'gstart';
    if (isSpecialA && !isSpecialB) return -1;
    if (!isSpecialA && isSpecialB) return 1;
    return (a.y ?? 0) - (b.y ?? 0) || (a.x ?? 0) - (b.x ?? 0);
  });

  const newLayout: Layout[] = [];
  sortedLayout.forEach((item) => {
    const widget = widgetsList.find((w) => w.label === item.i);
    const isSpecial =
      item.i === 'dash-stats' || item.i === 'news' || item.i === 'gstart';

    const w = isSpecial ? (item.w ?? cols) : getDefaultWidgetWidth(widget, cols);
    const h = isSpecial ? (item.h ?? 2) : getDefaultWidgetHeight(widget);
    const { x, y } = findNextHorizontalSlot(newLayout, w, h, cols);
    newLayout.push({
      ...item,
      x,
      y,
      w,
      h,
      minW: widget?.minWidth ?? 1,
      minH: widget?.minHeight ?? 2
    });
  });
  return newLayout;
}

export default function DashboardLayout() {
  const user = useUserState();
  const { colorScheme } = useMantineColorScheme();
  const isDark = colorScheme === 'dark';

  // Dashboard layout definition
  const [layouts, setLayouts] = useState({});
  // Dashboard widget selection
  const [widgets, setWidgets] = useState<DashboardWidgetProps[]>([]);

  // local/remote storage values for widget / layout
  const [
    remoteWidgets,
    setRemoteWidgets,
    remoteLayouts,
    setRemoteLayouts,
    showSampleDashboard,
    setShowSampleDashboard
  ] = useLocalState(
    useShallow((state) => [
      state.widgets,
      state.setWidgets,
      state.layouts,
      state.setLayouts,
      state.showSampleDashboard,
      state.setShowSampleDashboard
    ])
  );

  const [editing, setEditing] = useDisclosure(false);
  const [removing, setRemoving] = useDisclosure(false);

  const [
    widgetDrawerOpened,
    { open: openWidgetDrawer, close: closeWidgetDrawer }
  ] = useDisclosure(false);

  const [loaded, setLoaded] = useState(false);

  // Keyboard shortcut for editing the dashboard layout
  useInvenTreeHotkeys([
    [
      'mod+E',
      t`Toggle dashboard edit mode`,
      () => {
        setEditing.toggle();
      }
    ]
  ]);

  // Load available widgets
  const availableWidgets = useDashboardItems();

  const widgetLabels = useMemo(() => {
    return widgets.map((widget: DashboardWidgetProps) => widget.label);
  }, [widgets]);

  // Save the selected widgets to local storage when the selection changes
  useEffect(() => {
    if (loaded) {
      setRemoteWidgets(widgetLabels);
    }
  }, [widgetLabels]);

  /**
   * Callback function to add a new widget to the dashboard
   * Places widgets horizontally left-to-right across available columns
   */
  const addWidget = useCallback(
    (widget: string) => {
      const newWidget = availableWidgets.items.find(
        (wid) => wid.label === widget
      );

      if (!newWidget) {
        return;
      }

      if (widgets.some((w) => w.label === widget)) {
        return;
      }

      if (showSampleDashboard) {
        setShowSampleDashboard(false);
      }

      const nextWidgets = [...widgets, newWidget];
      setWidgets(nextWidgets);

      // Explicitly compute horizontal position (left-to-right) for the new widget across all breakpoints
      const _layouts: any = { ...layouts };

      Object.keys(BREAKPOINT_COLS).forEach((bp) => {
        const cols = BREAKPOINT_COLS[bp];
        const w = getDefaultWidgetWidth(newWidget, cols);
        const h = getDefaultWidgetHeight(newWidget);
        const bpLayout = (_layouts[bp] ?? []).filter(
          (item: Layout) => item.i !== widget
        );
        const { x, y } = findNextHorizontalSlot(bpLayout, w, h, cols);

        _layouts[bp] = [
          ...bpLayout,
          {
            i: widget,
            x,
            y,
            w,
            h,
            minW: newWidget.minWidth ?? 1,
            minH: newWidget.minHeight ?? 1
          }
        ];
      });

      setLayouts(_layouts);
      setRemoteLayouts(_layouts);
    },
    [availableWidgets.items, widgets, layouts, showSampleDashboard]
  );

  /**
   * Callback function to remove a widget from the dashboard
   */
  const removeWidget = useCallback(
    (widget: string) => {
      // Remove the widget from the list
      setWidgets(widgets.filter((item) => item.label !== widget));

      // Remove the widget from the layout
      const _layouts: any = { ...layouts };

      Object.keys(_layouts).forEach((key) => {
        _layouts[key] = _layouts[key].filter(
          (item: Layout) => item.i !== widget
        );
      });

      setLayouts(_layouts);
    },
    [widgets, layouts]
  );

  // When the layout is rendered, ensure that the widget attributes are observed
  const updateLayoutForWidget = useCallback(
    (layout: any[], widgets: any[], overrideSize: boolean) => {
      return layout.map((item: Layout): Layout => {
        // Find the matching widget
        const widget = widgets.find(
          (widget: DashboardWidgetProps) => widget.label === item.i
        );

        const minH = widget?.minHeight ?? 2;
        const minW = widget?.minWidth ?? 1;

        let w = Math.max(item.w ?? 1, minW);
        let h = Math.max(item.h ?? 1, minH);

        if (overrideSize) {
          w = minW;
          h = minH;
        }

        return {
          ...item,
          w: w,
          h: h,
          minH: minH,
          minW: minW
        };
      });
    },
    []
  );

  // Rebuild layout when the widget list changes
  useEffect(() => {
    onLayoutChange({}, layouts);
  }, [widgets]);

  const onLayoutChange = useCallback(
    (layout: any, newLayouts: any) => {
      // Reconstruct layouts based on the widget requirements
      Object.keys(newLayouts).forEach((key) => {
        newLayouts[key] = updateLayoutForWidget(
          newLayouts[key],
          widgets,
          false
        );
      });

      if (layouts && loaded && availableWidgets.loaded) {
        const reducedLayouts: any = {};
        // Reduce the layouts to exclude default attributes from the dataset
        Object.keys(newLayouts).forEach((key) => {
          reducedLayouts[key] = newLayouts[key].map((item: Layout) => {
            return {
              ...item,
              moved: item.moved ? true : undefined,
              static: item.static ? true : undefined
            };
          });
        });
        setRemoteLayouts(reducedLayouts);
        setLayouts(newLayouts);
      }
    },
    [loaded, widgets, availableWidgets.loaded]
  );

  const overviewWidgetLabels = useMemo(
    () => ['dash-stats'],
    []
  );

  const defaultLayouts: any = useMemo(() => {
    const lgLayouts: Layout[] = [
      // Top row: Stats (x: 0, w: 12)
      { w: 12, h: 2, x: 0, y: 0, i: 'dash-stats', minW: 6, minH: 2, moved: false, static: false }
    ];

    if (user.isSuperuser()) {
      lgLayouts.push({
        w: 12,
        h: 4,
        x: 0,
        y: 2,
        i: 'news',
        minW: 4,
        minH: 3,
        moved: false,
        static: false
      });
    }

    const mdLayouts: Layout[] = [
      { w: 10, h: 2, x: 0, y: 0, i: 'dash-stats', minW: 5, minH: 2, moved: false, static: false }
    ];

    const smLayouts: Layout[] = [
      { w: 6, h: 2, x: 0, y: 0, i: 'dash-stats', minW: 3, minH: 2, moved: false, static: false }
    ];

    return {
      lg: lgLayouts,
      md: mdLayouts,
      sm: smLayouts,
      xs: smLayouts.map((l) => ({ ...l, w: 4 })),
      xxs: smLayouts.map((l) => ({ ...l, w: 2 }))
    };
  }, [user]);

  const defaultWidgets = useMemo(() => {
    const targetLabels = user.isSuperuser()
      ? [...overviewWidgetLabels, 'news']
      : overviewWidgetLabels;
    return targetLabels
      .map((lwid: string) =>
        availableWidgets.items.find((wid) => wid.label === lwid)
      )
      .filter((widget): widget is DashboardWidgetProps => widget !== undefined);
  }, [availableWidgets.items, overviewWidgetLabels, user]);

  // Load the dashboard layout from local storage, ensuring overview widgets are preserved
  useEffect(() => {
    if (availableWidgets.loaded) {
      // Gather active labels: ensure core overview widgets are always included alongside user widgets
      const targetLabels = new Set<string>();
      overviewWidgetLabels.forEach((l) => targetLabels.add(l));
      remoteWidgets
        .filter((l) => !REMOVED_WIDGET_LABELS.has(l))
        .forEach((l) => targetLabels.add(l));

      const loadedWidgets = Array.from(targetLabels)
        .map((label) => availableWidgets.items.find((w) => w.label === label))
        .filter((w): w is DashboardWidgetProps => !!w);

      const fixedLayouts: any = {};

      Object.keys(BREAKPOINT_COLS).forEach((bp) => {
        const bpDefault: Layout[] = defaultLayouts[bp] ?? [];
        const bpRemoteRaw: Layout[] = (remoteLayouts as any)?.[bp] ?? [];
        const bpRemote: Layout[] = bpRemoteRaw.filter(
          (item: any) => !REMOVED_WIDGET_LABELS.has(item?.i)
        );

        const hasLegacyOverview = bpRemoteRaw.some(
          (item: any) =>
            REMOVED_WIDGET_LABELS.has(item?.i) ||
            (bp === 'lg' && item?.i === 'dash-stats' && (item?.w ?? 0) < 12)
        );

        const layoutMap = new Map<string, Layout>();
        bpDefault.forEach((item) => layoutMap.set(item.i, item));
        bpRemote.forEach((item) => {
          if (item && item.i) {
            // Keep user-positioned widget if valid, unless it's a legacy overview item needing updated geometry
            if (hasLegacyOverview && overviewWidgetLabels.includes(item.i)) {
              return;
            }
            layoutMap.set(item.i, item);
          }
        });

        const bpLayout: Layout[] = [];
        loadedWidgets.forEach((w) => {
          if (layoutMap.has(w.label)) {
            bpLayout.push(layoutMap.get(w.label)!);
          } else {
            const cols = BREAKPOINT_COLS[bp];
            const width = getDefaultWidgetWidth(w, cols);
            const height = getDefaultWidgetHeight(w);
            const { x, y } = findNextHorizontalSlot(bpLayout, width, height, cols);
            bpLayout.push({
              i: w.label,
              x,
              y,
              w: width,
              h: height,
              minW: w.minWidth ?? 1,
              minH: w.minHeight ?? 1
            });
          }
        });

        fixedLayouts[bp] = normalizeLayoutHorizontally(
          bpLayout,
          loadedWidgets,
          BREAKPOINT_COLS[bp]
        );
      });

      setLayouts(fixedLayouts);
      setWidgets(loadedWidgets);
      setLoaded(true);
      setRemoteLayouts(fixedLayouts);
    }
  }, [availableWidgets.loaded]);

  // Clear / reset all widgets from the dashboard
  const clearWidgets = useCallback(() => {
    setWidgets(defaultWidgets);
    setLayouts(defaultLayouts);
    setRemoteWidgets(overviewWidgetLabels);
    setRemoteLayouts(defaultLayouts);
  }, [defaultWidgets, defaultLayouts, overviewWidgetLabels]);

  return (
    <>
      <DashboardWidgetDrawer
        opened={widgetDrawerOpened}
        onClose={closeWidgetDrawer}
        onAddWidget={addWidget}
        currentWidgets={widgetLabels}
      />
      <DashboardMenu
        onAddWidget={openWidgetDrawer}
        onStartEdit={setEditing.open}
        onClear={clearWidgets}
        onStartRemove={setRemoving.open}
        onAcceptLayout={() => {
          setEditing.close();
          setRemoving.close();
        }}
        editing={editing}
        removing={removing}
      />
      <Space h='xs' />
      {availableWidgets.error && (
        <Alert color='red' title={t`Error`} icon={<IconExclamationCircle />}>
          {t`Failed to load dashboard widgets.`}
        </Alert>
      )}
      {layouts && loaded && availableWidgets.loaded ? (
        <>
          {widgetLabels.length === 0 ? (
            <Center>
              <Card
                shadow='sm'
                padding='xl'
                radius='lg'
                style={{
                  width: '100%',
                  background: isDark ? '#1e293b' : '#ffffff',
                  border: isDark ? '1px solid rgba(255,255,255,0.08)' : '1.5px solid #e2e8f0',
                  borderRadius: 20,
                  boxShadow: isDark
                    ? '0 10px 25px -4px rgba(0, 0, 0, 0.35)'
                    : '0 10px 30px -5px rgba(15, 23, 42, 0.05)'
                }}
              >
                <Alert
                  color='blue'
                  title={t`No Widgets Selected`}
                  icon={<IconInfoCircle size={20} />}
                  radius='md'
                  style={{
                    background: isDark
                      ? 'rgba(2, 132, 199, 0.12)'
                      : 'linear-gradient(135deg, rgba(224, 242, 254, 0.6) 0%, rgba(186, 230, 253, 0.4) 100%)',
                    border: isDark
                      ? '1px solid rgba(56, 189, 248, 0.25)'
                      : '1.5px solid #bae6fd',
                    color: isDark ? '#38bdf8' : '#0369a1'
                  }}
                >
                  <Text size='sm' c={isDark ? '#cbd5e1' : '#334155'} mb='xs'>
                    {t`Use the menu to add widgets to the dashboard`}
                  </Text>
                  <Button variant='light' color='blue' size='xs' onClick={clearWidgets}>
                    {t`Restore Default Dashboard`}
                  </Button>
                </Alert>
              </Card>
            </Center>
          ) : (
            WidgetGrid(
              layouts,
              onLayoutChange,
              editing,
              widgets,
              removing,
              removeWidget
            )
          )}
        </>
      ) : (
        <Center>
          <Loader size='xl' />
        </Center>
      )}
    </>
  );
}

function WidgetGrid(
  layouts: {},
  onLayoutChange: (layout: any, newLayouts: any) => void,
  editing: boolean,
  widgets: DashboardWidgetProps[],
  removing: boolean,
  removeWidget: (widget: string) => void
) {
  return (
    <ReactGridLayout
      className='dashboard-layout'
      breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
      cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
      rowHeight={64}
      layouts={layouts}
      onLayoutChange={onLayoutChange}
      compactType={'vertical'}
      isDraggable={editing}
      isResizable={editing}
      draggableCancel='input, textarea, select, .mantine-ActionIcon-root, .mantine-Menu-dropdown'
      margin={[12, 12]}
      containerPadding={[0, 0]}
      resizeHandles={['ne', 'se', 'sw', 'nw']}
    >
      {widgets.map((item: DashboardWidgetProps) => {
        return DashboardWidget({
          item: item,
          editing: editing,
          removing: removing,
          onRemove: () => {
            removeWidget(item.label);
          }
        });
      })}
    </ReactGridLayout>
  );
}
