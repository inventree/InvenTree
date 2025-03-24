import { t } from '@lingui/macro';
import { Group } from '@mantine/core';

import { StylishText } from '@lib/components';
import type { DashboardWidgetProps } from '../../../../lib/components/dashboard/DashboardWidget';
import { ColorToggle } from '../../items/ColorToggle';

function ColorToggleWidget(title: string) {
  return (
    <Group justify='space-between' wrap='nowrap'>
      <StylishText size='lg'>{title}</StylishText>
      <ColorToggle />
    </Group>
  );
}

export default function ColorToggleDashboardWidget(): DashboardWidgetProps {
  const title = t`Change Color Mode`;

  return {
    label: 'clr',
    title: title,
    description: t`Change the color mode of the user interface`,
    minHeight: 1,
    minWidth: 2,
    render: () => ColorToggleWidget(title)
  };
}
