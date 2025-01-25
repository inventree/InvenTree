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

export default function Calendar(props: InvenTreeCalendarProps) {
  const [monthSelectOpened, setMonthSelectOpened] = useState<boolean>(false);

  const [locale] = useLocalState((s) => [s.language]);

  const selectMonth = useCallback(
    (date: DateValue) => {
      props.state.selectMonth(date);
      setMonthSelectOpened(false);
    },
    [props.state.selectMonth]
  );

  // Callback when the calendar date range is adjusted
  const datesSet = useCallback(
    (dateInfo: DatesSetArg) => {
      if (props.state.ref?.current) {
        const api = props.state.ref.current.getApi();

        // Update calendar state
        props.state.setMonthName(api.view.title);
        props.state.setStartDate(dateInfo.start);
        props.state.setEndDate(dateInfo.end);
      }

      // Pass the dates set to the parent component
      props.datesSet?.(dateInfo);
    },
    [props.datesSet, props.state.ref, props.state.setMonthName]
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
            onClick={props.state.prevMonth}
            tooltipAlignment='top'
            tooltip={t`Previous month`}
          />
          <ActionButton
            icon={<IconCalendarDot />}
            onClick={props.state.currentMonth}
            tooltipAlignment='top'
            tooltip={t`Today`}
          />
          <ActionButton
            icon={<IconChevronRight />}
            onClick={props.state.nextMonth}
            tooltipAlignment='top'
            tooltip={t`Next month`}
          />
          <StylishText size='lg'>{props.state.monthName}</StylishText>
        </Group>
        <Group justify='right' gap='xs' wrap='nowrap'>
          {(props.enableSearch ?? true) && (
            <TableSearchInput searchCallback={props.state.setSearchTerm} />
          )}
        </Group>
      </Group>
      <Box pos='relative'>
        <LoadingOverlay visible={props.isLoading} />
        <FullCalendar
          ref={props.state.ref}
          plugins={[dayGridPlugin]}
          initialView='dayGridMonth'
          locales={allLocales}
          locale={locale}
          headerToolbar={false}
          footerToolbar={false}
          {...props}
          datesSet={datesSet}
        />
      </Box>
    </Stack>
  );
}
