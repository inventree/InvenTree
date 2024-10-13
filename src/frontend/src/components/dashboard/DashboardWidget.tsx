import { Box, Indicator, Overlay, Paper } from '@mantine/core';
import { IconX } from '@tabler/icons-react';

import { Boundary } from '../Boundary';

/**
 * Dashboard widget properties.
 *
 * @param title The title of the widget
 * @param visible A function that returns whether the widget should be visible
 * @param render A function that renders the widget
 */
export interface DashboardWidgetProps {
  label: string;
  title: string;
  description: string;
  minWidth?: number;
  minHeight?: number;
  render: () => JSX.Element;
  visible?: () => boolean;
}

/**
 * Wrapper for a dashboard widget.
 */
export default function DashboardWidget({
  item,
  editing
}: {
  item: DashboardWidgetProps;
  editing: boolean;
}) {
  // TODO: Implement visibility check
  //     if (!props?.visible?.() == false) {
  //     return null;
  //   }

  // TODO: Add button to remove widget (if "editing")

  return (
    <Paper withBorder key={item.label} shadow="sm" p="xs">
      <Boundary label={`dashboard-widget-${item.label}`}>
        <Box
          key={`dashboard-widget-${item.label}`}
          style={{
            width: '100%',
            height: '100%',
            padding: '0px',
            margin: '0px'
          }}
        >
          {item.render()}
        </Box>
      </Boundary>
    </Paper>
  );
}
