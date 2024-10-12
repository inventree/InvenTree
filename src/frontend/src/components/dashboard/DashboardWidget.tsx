import { Paper } from '@mantine/core';

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
  minWidth?: number;
  minHeight?: number;
  render: () => JSX.Element;
  visible?: () => boolean;
}

/**
 * Wrapper for a dashboard widget.
 */
export default function DashboardWidget(props: DashboardWidgetProps) {
  // TODO: Implement visibility check
  //     if (!props?.visible?.() == false) {
  //     return null;
  //   }

  return (
    <Paper withBorder key={props.label} shadow="sm" p="xs">
      <Boundary label={`dashboard-widget-${props.label}`}>
        {props.render()}
      </Boundary>
    </Paper>
  );
}
