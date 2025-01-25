import type { CalendarOptions, DatesSetArg } from '@fullcalendar/core';
import allLocales from '@fullcalendar/core/locales-all';
import dayGridPlugin from '@fullcalendar/daygrid';
import FullCalendar from '@fullcalendar/react';
import { t } from '@lingui/macro';
import {
  Box,
  Button,
  Group,
  LoadingOverlay,
  Popover,
  Stack,
  Tooltip
} from '@mantine/core';
import { type DateValue, MonthPicker } from '@mantine/dates';
import {
  IconCalendarDot,
  IconCalendarMonth,
  IconChevronLeft,
  IconChevronRight
} from '@tabler/icons-react';
import { useCallback, useState } from 'react';
import type { CalendarState } from '../../hooks/UseCalendar';
import { useLocalState } from '../../states/LocalState';
import { TableSearchInput } from '../../tables/Search';
import { ActionButton } from '../buttons/ActionButton';
import { StylishText } from '../items/StylishText';

export interface InvenTreeCalendarProps extends CalendarOptions {
  state: CalendarState;
  isLoading?: boolean;
  enableSearch?: boolean;
}

export default function Calendar({
  state,
  isLoading,
  enableSearch,
  ...calendarProps
}: InvenTreeCalendarProps) {
  const [monthSelectOpened, setMonthSelectOpened] = useState<boolean>(false);

  const [locale] = useLocalState((s) => [s.language]);

  const selectMonth = useCallback(
    (date: DateValue) => {
      state.selectMonth(date);
      setMonthSelectOpened(false);
    },
    [state.selectMonth]
  );

  // Callback when the calendar date range is adjusted
  const datesSet = useCallback(
    (dateInfo: DatesSetArg) => {
      if (state.ref?.current) {
        const api = state.ref.current.getApi();

        // Update calendar state
        state.setMonthName(api.view.title);
        state.setStartDate(dateInfo.start);
        state.setEndDate(dateInfo.end);
      }

      // Pass the dates set to the parent component
      calendarProps.datesSet?.(dateInfo);
    },
    [calendarProps.datesSet, state.ref, state.setMonthName]
  );

  return (
    <Stack gap='xs'>
      <Group justify='space-between' gap='xs'>
        <Group gap='xs' justify='left'>
          <Popover
            opened={monthSelectOpened}
            onClose={() => setMonthSelectOpened(false)}
            position='bottom-start'
            shadow='md'
          >
            <Popover.Target>
              <Tooltip label={t`Select month`} position='top'>
                <Button
                  m={0}
                  variant='transparent'
                  onClick={() => {
                    setMonthSelectOpened(!monthSelectOpened);
                  }}
                >
                  <IconCalendarMonth />
                </Button>
              </Tooltip>
            </Popover.Target>
            <Popover.Dropdown>
              <MonthPicker onChange={selectMonth} />
            </Popover.Dropdown>
          </Popover>
          <ActionButton
            icon={<IconChevronLeft />}
            onClick={state.prevMonth}
            tooltipAlignment='top'
            tooltip={t`Previous month`}
          />
          <ActionButton
            icon={<IconCalendarDot />}
            onClick={state.currentMonth}
            tooltipAlignment='top'
            tooltip={t`Today`}
          />
          <ActionButton
            icon={<IconChevronRight />}
            onClick={state.nextMonth}
            tooltipAlignment='top'
            tooltip={t`Next month`}
          />
          <StylishText size='lg'>{state.monthName}</StylishText>
        </Group>
        <Group justify='right' gap='xs' wrap='nowrap'>
          {(enableSearch ?? true) && (
            <TableSearchInput searchCallback={state.setSearchTerm} />
          )}
        </Group>
      </Group>
      <Box pos='relative'>
        <LoadingOverlay visible={isLoading} />
        <FullCalendar
          ref={state.ref}
          plugins={[dayGridPlugin]}
          initialView='dayGridMonth'
          locales={allLocales}
          locale={locale}
          headerToolbar={false}
          footerToolbar={false}
          {...calendarProps}
          datesSet={datesSet}
        />
      </Box>
    </Stack>
  );
}
