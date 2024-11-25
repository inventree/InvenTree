import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';

import { LanguageSelect } from '../../items/LanguageSelect';
import { StylishText } from '../../items/StylishText';
import type { DashboardWidgetProps } from '../DashboardWidget';

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
