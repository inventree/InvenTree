import { Center, Divider, Loader, Paper, Text } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { ReactNode, useCallback, useEffect, useMemo, useState } from 'react';
import { Layout, Responsive, WidthProvider } from 'react-grid-layout';

import { Boundary } from '../Boundary';
import DashboardMenu from './DashboardMenu';

const ReactGridLayout = WidthProvider(Responsive);

/**
 * Dashboard item properties. Describes a current item in the dashboard.
 */

export interface DashboardItemProps {
  label: string;
  widget: ReactNode; // DashboardWidgetProps;
  width?: number;
  height?: number;
}

// Default items for the dashboard
function getDefaultItems(): DashboardItemProps[] {
  return [
    {
      label: 'widget-1',
      width: 2,
      height: 1,
      widget: <Text>Widget 1</Text>
    },
    {
      label: 'widget-2',
      width: 5,
      height: 2,
      widget: <Text>Widget 2</Text>
    },
    {
      label: 'widget-3',
      width: 4,
      height: 3,
      widget: <Text>Widget 3</Text>
    },
    {
      label: 'widget-4',
      width: 4,
      widget: <Text>Widget 4</Text>
    }
  ];
}

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

  const widgets = useMemo(() => getDefaultItems(), []);

  // When the layout is rendered, ensure that the widget attributes are observed
  const updateLayoutForWidget = useCallback(
    (layout: any[]) => {
      return layout.map((item: Layout): Layout => {
        // Find the matching widget
        let widget = widgets.find((widget) => widget.label === item.i);

        const minH = widget?.height ?? 2;
        const minW = widget?.width ?? 1;

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
          {widgets.map((item) => {
            return DashboardLayoutItem(item);
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

/**
 * Wrapper for a dashboard item
 */
function DashboardLayoutItem(item: DashboardItemProps) {
  return (
    <Paper withBorder key={item.label} p="xs" shadow="sm">
      <Boundary label={`dashboard-item-${item.label}`}>{item.widget}</Boundary>
    </Paper>
  );
}
