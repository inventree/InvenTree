import type { CalendarOptions, DatesSetArg } from '@fullcalendar/core';
import allLocales from '@fullcalendar/core/locales-all';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import FullCalendar from '@fullcalendar/react';

import type { TableFilter } from '@lib/types/Filters';
import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Box,
  Button,
  Group,
  Indicator,
  LoadingOverlay,
  Popover,
  Stack,
  Tooltip
} from '@mantine/core';
import { type DateValue, MonthPicker } from '@mantine/dates';
import {
  IconCalendarMonth,
  IconChevronLeft,
  IconChevronRight,
  IconDownload,
  IconFilter
} from '@tabler/icons-react';
import { useCallback, useState } from 'react';
import type { CalendarState } from '../../hooks/UseCalendar';
import { useLocalState } from '../../states/LocalState';
import { FilterSelectDrawer } from '../../tables/FilterSelectDrawer';
import { TableSearchInput } from '../../tables/Search';
import { Boundary } from '../Boundary';
import { ActionButton } from '../buttons/ActionButton';
import { StylishText } from '../items/StylishText';

export interface InvenTreeCalendarProps extends CalendarOptions {
  enableDownload?: boolean;
  enableFilters?: boolean;
  enableSearch?: boolean;
  filters?: TableFilter[];
  isLoading?: boolean;
  state: CalendarState;
}

export default function Calendar({
  enableDownload,
  enableFilters = false,
  enableSearch,
  isLoading,
  filters,
  state,
  ...calendarProps
}: InvenTreeCalendarProps) {
  const [monthSelectOpened, setMonthSelectOpened] = useState<boolean>(false);

  const [filtersVisible, setFiltersVisible] = useState<boolean>(false);

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
    <>
      {state.exportModal.modal}
      {enableFilters && filters && (filters?.length ?? 0) > 0 && (
        <Boundary label={`InvenTreeCalendarFilterDrawer-${state.name}`}>
          <FilterSelectDrawer
            title={t`Calendar Filters`}
            availableFilters={filters}
            filterSet={state.filterSet}
            opened={filtersVisible}
            onClose={() => setFiltersVisible(false)}
          />
        </Boundary>
      )}
      <Stack gap='xs'>
        <Group justify='space-between' gap='xs'>
          <Group gap={0} justify='left'>
            <ActionButton
              icon={<IconChevronLeft />}
              onClick={state.prevMonth}
              tooltipAlignment='top'
              tooltip={t`Previous month`}
            />
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
                    aria-label='calendar-select-month'
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
              icon={<IconChevronRight />}
              onClick={state.nextMonth}
              tooltipAlignment='top'
              tooltip={t`Next month`}
            />
            <StylishText size='lg'>{state.monthName}</StylishText>
          </Group>
          <Group justify='right' gap='xs' wrap='nowrap'>
            {enableSearch && (
              <TableSearchInput searchCallback={state.setSearchTerm} />
            )}
            {enableFilters && filters && filters.length > 0 && (
              <Indicator
                size='xs'
                label={state.filterSet.activeFilters?.length ?? 0}
                disabled={state.filterSet.activeFilters?.length == 0}
              >
                <ActionIcon
                  variant='transparent'
                  aria-label='calendar-select-filters'
                >
                  <Tooltip label={t`Calendar Filters`} position='top-end'>
                    <IconFilter
                      onClick={() => setFiltersVisible(!filtersVisible)}
                    />
                  </Tooltip>
                </ActionIcon>
              </Indicator>
            )}
            {enableDownload && (
              <ActionIcon
                variant='transparent'
                aria-label='calendar-export-data'
              >
                <Tooltip label={t`Download data`} position='top-end'>
                  <IconDownload onClick={state.exportModal.open} />
                </Tooltip>
              </ActionIcon>
            )}
          </Group>
        </Group>
        <Box pos='relative'>
          <LoadingOverlay visible={state.query.isFetching} />
          <FullCalendar
            ref={state.ref}
            plugins={[dayGridPlugin, interactionPlugin]}
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
    </>
  );
}
