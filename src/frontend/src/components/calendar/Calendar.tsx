import type { CalendarOptions } from '@fullcalendar/core';
import allLocales from '@fullcalendar/core/locales-all';
import dayGridPlugin from '@fullcalendar/daygrid';
import FullCalendar from '@fullcalendar/react';
import { t } from '@lingui/macro';
import { Group, Stack } from '@mantine/core';
import {
  IconCalendarDot,
  IconChevronLeft,
  IconChevronRight
} from '@tabler/icons-react';
import { useLocalState } from '../../states/LocalState';
import { ActionButton } from '../buttons/ActionButton';
import { StylishText } from '../items/StylishText';

export default function Calendar(props: CalendarOptions) {
  const [locale] = useLocalState((s) => [s.language]);

  return (
    <Stack gap='xs'>
      <Group justify='space-between' gap='xs'>
        <Group gap='xs' justify='left'>
          <ActionButton
            icon={<IconChevronLeft />}
            onClick={() => {}}
            tooltipAlignment='top'
            tooltip={t`Previous month`}
          />
          <ActionButton
            icon={<IconCalendarDot />}
            onClick={() => {}}
            tooltipAlignment='top'
            tooltip={t`Today`}
          />
          <ActionButton
            icon={<IconChevronRight />}
            onClick={() => {}}
            tooltipAlignment='top'
            tooltip={t`Next month`}
          />
        </Group>
        <StylishText size='lg'>MONTHY</StylishText>
        <Group justify='right' gap='xs' wrap='nowrap'>
          <div>hello world</div>
        </Group>
      </Group>
      <FullCalendar
        plugins={[dayGridPlugin]}
        initialView='dayGridMonth'
        locales={allLocales}
        locale={locale}
        headerToolbar={false}
        footerToolbar={false}
        {...props}
      />
    </Stack>
  );
}
