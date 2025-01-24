import type { CalendarOptions, DatesSetArg } from '@fullcalendar/core';
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
import { useCallback, useRef, useState } from 'react';
import { useLocalState } from '../../states/LocalState';
import { ActionButton } from '../buttons/ActionButton';
import { StylishText } from '../items/StylishText';

export default function Calendar(props: CalendarOptions) {
  const calendarRef = useRef<FullCalendar | null>(null);

  const [locale] = useLocalState((s) => [s.language]);

  const [monthName, setMonthName] = useState<string>('');

  // Navigate to the previous month
  const prevMonth = useCallback(() => {
    calendarRef.current?.getApi().prev();
  }, [calendarRef]);

  // Navigate to the next month
  const nextMonth = useCallback(() => {
    calendarRef.current?.getApi().next();
  }, [calendarRef]);

  // Navigate to the current month
  const currentMonth = useCallback(() => {
    calendarRef.current?.getApi().today();
  }, [calendarRef]);

  // Callback when the calendar date range is adjusted
  const datesSet = useCallback(
    (dateInfo: DatesSetArg) => {
      if (calendarRef?.current) {
        const api = calendarRef.current.getApi();

        setMonthName(api.view.title);
      }

      // Pass the dates set to the parent component
      props.datesSet?.(dateInfo);
    },
    [calendarRef, props.datesSet, setMonthName]
  );

  return (
    <Stack gap='xs'>
      <Group justify='space-between' gap='xs'>
        <Group gap='xs' justify='left'>
          <ActionButton
            icon={<IconChevronLeft />}
            onClick={prevMonth}
            tooltipAlignment='top'
            tooltip={t`Previous month`}
          />
          <ActionButton
            icon={<IconCalendarDot />}
            onClick={currentMonth}
            tooltipAlignment='top'
            tooltip={t`Today`}
          />
          <ActionButton
            icon={<IconChevronRight />}
            onClick={nextMonth}
            tooltipAlignment='top'
            tooltip={t`Next month`}
          />
        </Group>
        <StylishText size='lg'>{monthName}</StylishText>
        <Group justify='right' gap='xs' wrap='nowrap'>
          <div>hello world</div>
        </Group>
      </Group>
      <FullCalendar
        ref={calendarRef}
        plugins={[dayGridPlugin]}
        initialView='dayGridMonth'
        locales={allLocales}
        locale={locale}
        headerToolbar={false}
        footerToolbar={false}
        {...props}
        datesSet={datesSet}
      />
    </Stack>
  );
}
