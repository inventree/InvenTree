import { Center, Divider, Loader } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Layout, Responsive, WidthProvider } from 'react-grid-layout';

import { useUserState } from '../../states/UserState';
import DashboardMenu from './DashboardMenu';
import DashboardWidget, { DashboardWidgetProps } from './DashboardWidget';
import DashboardWidgetDrawer from './DashboardWidgetDrawer';
import AvailableDashboardWidgets from './DashboardWidgetLibrary';

const ReactGridLayout = WidthProvider(Responsive);

/**
 * Save the dashboard layout to local storage
 */
function saveDashboardLayout(layouts: any, userId: number | undefined): void {
  const data = JSON.stringify(layouts);

  if (userId) {
    localStorage?.setItem(`dashboard-layout-${userId}`, data);
  }

  localStorage?.setItem('dashboard-layout', data);
}

/**
 * Load the dashboard layout from local storage
 */
function loadDashboardLayout(
  userId: number | undefined
): Record<string, Layout[]> {
  let layout = userId && localStorage?.getItem(`dashboard-layout-${userId}`);

  if (!layout) {
    // Fallback to global layout
    layout = localStorage?.getItem('dashboard-layout');
  }

  if (layout) {
    return JSON.parse(layout);
  } else {
    return {};
  }
}

/**
 * Save the list of selected widgets to local storage
 */
function saveDashboardWidgets(
  widgets: string[],
  userId: number | undefined
): void {
  const data = JSON.stringify(widgets);

  if (userId) {
    localStorage?.setItem(`dashboard-widgets-${userId}`, data);
  }

  localStorage?.setItem('dashboard-widgets', data);
}

/**
 * Load the list of selected widgets from local storage
 */
function loadDashboardWidgets(userId: number | undefined): string[] {
  let widgets = userId && localStorage?.getItem(`dashboard-widgets-${userId}`);

  if (!widgets) {
    // Fallback to global widget list
    widgets = localStorage?.getItem('dashboard-widgets');
  }

  if (widgets) {
    return JSON.parse(widgets);
  } else {
    return [];
  }
}

export default function DashboardLayout({}: {}) {
  const user = useUserState();

  // Dashboard layout definition
  const [layouts, setLayouts] = useState({});

  // Dashboard widget selection
  const [widgets, setWidgets] = useState<DashboardWidgetProps[]>([]);

  const [editable, setEditable] = useDisclosure(false);

  const [
    widgetDrawerOpened,
    { open: openWidgetDrawer, close: closeWidgetDrawer }
  ] = useDisclosure(false);

  const [loaded, setLoaded] = useState(false);

  // Memoize all available widgets
  const allWidgets: DashboardWidgetProps[] = useMemo(
    () => AvailableDashboardWidgets(),
    []
  );

  // Initial widget selection
  useEffect(() => {
    setWidgets(allWidgets.filter((widget, index) => index < 5));
  }, []);

  const widgetLabels = useMemo(() => {
    return widgets.map((widget: DashboardWidgetProps) => widget.label);
  }, [widgets]);

  // Save the selected widgets to local storage when the selection changes
  useEffect(() => {
    if (loaded) {
      saveDashboardWidgets(widgetLabels, user.userId());
    }
  }, [widgetLabels]);

  const addWidget = useCallback(
    (widget: string) => {
      let newWidget = allWidgets.find((wid) => wid.label === widget);

      if (newWidget) {
        setWidgets([...widgets, newWidget]);
      }

      // Update the layouts to include the new widget (and enforce initial size)
      let _layouts: any = { ...layouts };

      Object.keys(_layouts).forEach((key) => {
        _layouts[key] = updateLayoutForWidget(_layouts[key], true);
      });

      setLayouts(_layouts);
    },
    [allWidgets, widgets, layouts]
  );

  // When the layout is rendered, ensure that the widget attributes are observed
  const updateLayoutForWidget = useCallback(
    (layout: any[], overrideSize: boolean) => {
      return layout.map((item: Layout): Layout => {
        // Find the matching widget
        let widget = widgets.find(
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
    [widgets]
  );

  // Rebuild layout when the widget list changes
  useEffect(() => {
    onLayoutChange({}, layouts);
  }, [widgets]);

  const onLayoutChange = useCallback(
    (layout: any, newLayouts: any) => {
      // Reconstruct layouts based on the widget requirements
      Object.keys(newLayouts).forEach((key) => {
        newLayouts[key] = updateLayoutForWidget(newLayouts[key], false);
      });

      if (layouts && loaded) {
        saveDashboardLayout(newLayouts, user.userId());
        setLayouts(newLayouts);
      }
    },
    [loaded]
  );

  // Load the dashboard layout from local storage
  useEffect(() => {
    const initialLayouts = loadDashboardLayout(user.userId());
    const initialWidgetLabels = loadDashboardWidgets(user.userId());

    setLayouts(initialLayouts);
    setWidgets(
      allWidgets.filter((widget) => initialWidgetLabels.includes(widget.label))
    );

    setLoaded(true);
  }, []);

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
        onToggleEdit={setEditable.toggle}
        editing={editable}
      />
      <Divider p="xs" />

      {layouts && loaded ? (
        <ReactGridLayout
          className="dashboard-layout"
          breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
          cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
          rowHeight={64}
          layouts={layouts}
          onLayoutChange={onLayoutChange}
          compactType={'vertical'}
          isDraggable={editable}
          isResizable={editable}
          margin={[10, 10]}
          containerPadding={[0, 0]}
          resizeHandles={['ne', 'se', 'sw', 'nw']}
        >
          {widgets.map((item: DashboardWidgetProps) => {
            return DashboardWidget({
              item: item,
              editing: editable
            });
          })}
        </ReactGridLayout>
      ) : (
        <Center>
          <Loader size="xl" />
        </Center>
      )}
    </>
  );
}
