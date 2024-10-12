import { Center, Divider, Loader } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Layout, Responsive, WidthProvider } from 'react-grid-layout';

import DashboardMenu from './DashboardMenu';
import DashboardWidget, { DashboardWidgetProps } from './DashboardWidget';
import BuiltinDashboardWidgets from './DashboardWidgetLibrary';

const ReactGridLayout = WidthProvider(Responsive);

/**
 * Save the dashboard layout to local storage
 */
function saveDashboardLayout(layouts: any): void {
  localStorage?.setItem('dashboard-layout', JSON.stringify(layouts));
}

/**
 * Load the dashboard layout from local storage
 */
function loadDashboardLayout(): Record<string, Layout[]> {
  const layout = localStorage?.getItem('dashboard-layout');

  if (layout) {
    return JSON.parse(layout);
  } else {
    return {};
  }
}

export default function DashboardLayout({}: {}) {
  const [layouts, setLayouts] = useState({});
  const [editable, setEditable] = useDisclosure(false);
  const [loaded, setLoaded] = useState(false);

  const widgets = useMemo(() => {
    return BuiltinDashboardWidgets();
  }, []);

  // When the layout is rendered, ensure that the widget attributes are observed
  const updateLayoutForWidget = useCallback(
    (layout: any[]) => {
      return layout.map((item: Layout): Layout => {
        // Find the matching widget
        let widget = widgets.find((widget) => widget.label === item.i);

        const minH = widget?.minHeight ?? 2;
        const minW = widget?.minWidth ?? 1;

        const w = Math.max(item.w ?? 1, minW);
        const h = Math.max(item.h ?? 1, minH);

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
        newLayouts[key] = updateLayoutForWidget(newLayouts[key]);
      });

      if (layouts && loaded) {
        saveDashboardLayout(newLayouts);
        setLayouts(newLayouts);
      }
    },
    [loaded]
  );

  // Load the dashboard layout from local storage
  useEffect(() => {
    const initialLayouts = loadDashboardLayout();

    // onLayoutChange({}, initialLayouts);
    setLayouts(initialLayouts);

    setLoaded(true);
  }, []);

  return (
    <>
      <DashboardMenu onToggleEdit={setEditable.toggle} editing={editable} />
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
