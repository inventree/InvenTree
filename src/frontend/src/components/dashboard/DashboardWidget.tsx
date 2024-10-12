import { Card } from '@mantine/core';

import { Boundary } from '../Boundary';
import { StylishText } from '../items/StylishText';

/**
 * Dashboard widget properties.
 *
 * @param title The title of the widget
 * @param visible A function that returns whether the widget should be visible
 * @param render A function that renders the widget
 */
export interface DashboardWidgetProps {
  title: string;
  label: string;
  minWidth: number;
  minHeight: number;
  visible: () => boolean;
  render: () => JSX.Element;
  onClick?: (event: any) => void;
}

/**
 * Wrapper for a
 */
export default function DashboardWidget(props: DashboardWidgetProps) {
  if (!props.visible()) {
    return null;
  }

  return (
    <Boundary label={`dashboard-widget-${props.label}`}>
      <Card shadow="xs" p="sm">
        <Card.Section>
          <StylishText size="xl">{props.title}</StylishText>
        </Card.Section>
        {props.render()}
      </Card>
    </Boundary>
  );
}
