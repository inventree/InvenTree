import { t } from '@lingui/core/macro';
import { Stack } from '@mantine/core';

import { StylishText } from '@lib/components';
import type { DashboardWidgetProps } from '../../../../lib/components/dashboard/DashboardWidget';
import { LanguageSelect } from '../../items/LanguageSelect';

function LanguageSelectWidget(title: string) {
  return (
    <Stack gap='xs'>
      <StylishText size='lg'>{title}</StylishText>
      <LanguageSelect width={140} />
    </Stack>
  );
}

export default function LanguageSelectDashboardWidget(): DashboardWidgetProps {
  const title = t`Change Language`;

  return {
    label: 'lngsel',
    title: title,
    description: t`Change the language of the user interface`,
    minHeight: 1,
    minWidth: 2,
    render: () => LanguageSelectWidget(title)
  };
}
