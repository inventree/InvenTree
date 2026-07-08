import type {
  CalendarOptions,
  DatesSetArg,
  DayCellContentArg,
  EventContentArg
} from '@fullcalendar/core';
import allLocales from '@fullcalendar/core/locales-all';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import FullCalendar from '@fullcalendar/react';

import { ActionButton } from '@lib/components/ActionButton';
import { Boundary } from '@lib/components/Boundary';
import { SearchInput } from '@lib/components/SearchInput';
import { StylishText } from '@lib/components/StylishText';
import type { TableFilter } from '@lib/types/Filters';
import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Box,
  Button,
  Group,
  HoverCard,
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
  IconFilter,
  IconRefresh
} from '@tabler/icons-react';
import {
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState
} from 'react';
import { useShallow } from 'zustand/react/shallow';
import {
  defaultLocale,
  getPriorityLocale
} from '../../contexts/LanguageContext';
import type { CalendarState } from '../../hooks/UseCalendar';
import { useLocalState } from '../../states/LocalState';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { FilterSelectDrawer } from '../tables/FilterSelectDrawer';

export interface InvenTreeCalendarProps extends CalendarOptions {
  enableDownload?: boolean;
  enableFilters?: boolean;
  enableSearch?: boolean;
  enableRefresh?: boolean;
  eventTooltipContent?: (event: EventContentArg) => ReactNode;
  filters?: TableFilter[];
  isLoading?: boolean;
  state: CalendarState;
}

export default function Calendar({
  enableDownload,
  enableFilters = false,
  enableSearch,
  enableRefresh = true,
  eventTooltipContent,
  isLoading,
  filters,
  state,
  ...calendarProps
}: Readonly<InvenTreeCalendarProps>) {
  const globalSettings = useGlobalSettingsState();

  const horizonMonths = useMemo(
    () =>
      Number.parseInt(
        globalSettings.getSetting('CALENDAR_HORIZON_MONTHS') ?? '12',
        10
      ),
    [globalSettings]
  );

  // When the horizon is a single month, fall back to the standard month grid.
  const isScrollView = horizonMonths > 1;

  const [monthSelectOpened, setMonthSelectOpened] = useState<boolean>(false);

  const [filtersVisible, setFiltersVisible] = useState<boolean>(false);

  const [locale] = useLocalState(useShallow((s) => [s.language]));

  // Ensure underscore is replaced with dash
  const calendarLocale = useMemo(() => {
    let _locale: string | null = locale;

    if (!_locale) {
      _locale = getPriorityLocale();
    }

    _locale = _locale || defaultLocale;

    _locale = _locale.replace('_', '-');

    return _locale;
  }, [locale]);

  const selectMonth = useCallback(
    (date: DateValue) => {
      state.selectMonth(date);
      setMonthSelectOpened(false);
    },
    [state.selectMonth]
  );

  useEffect(() => {
    // Select initial month on first calendar render
    state.ref?.current?.getApi()?.gotoDate(new Date());
  }, []);

  // Callback when the calendar date range is adjusted
  const datesSet = useCallback(
    (dateInfo: DatesSetArg) => {
      if (state.ref?.current) {
        // Show the starting month of the view (advance 15 days past any padding days)
        const viewStart = new Date(dateInfo.start);
        viewStart.setDate(viewStart.getDate() + 15);
        const startMonthLabel = new Intl.DateTimeFormat(calendarLocale, {
          month: 'long',
          year: 'numeric'
        }).format(viewStart);

        state.setMonthName(startMonthLabel);
        state.setStartDate(dateInfo.start);
        state.setEndDate(dateInfo.end);
      }

      // Pass the dates set to the parent component
      calendarProps.datesSet?.(dateInfo);
    },
    [
      calendarLocale,
      calendarProps.datesSet,
      state.ref,
      state.setMonthName,
      state.setStartDate,
      state.setEndDate
    ]
  );

  const wrappedEventContent = useCallback(
    (arg: EventContentArg) => {
      const inner =
        typeof calendarProps.eventContent === 'function'
          ? calendarProps.eventContent(arg, null)
          : (calendarProps.eventContent ?? null);

      if (!eventTooltipContent) return inner;

      const tooltip = eventTooltipContent(arg);

      if (!tooltip) return inner;

      return (
        <HoverCard
          openDelay={1000}
          closeDelay={50}
          shadow='md'
          position='top-start'
        >
          <HoverCard.Target>
            <div style={{ width: '100%', overflow: 'hidden' }}>{inner}</div>
          </HoverCard.Target>
          <HoverCard.Dropdown>{tooltip}</HoverCard.Dropdown>
        </HoverCard>
      );
    },
    [calendarProps.eventContent, eventTooltipContent]
  );

  const scrollBoxRef = useRef<HTMLDivElement>(null);

  const updateMonthFromScroll = useCallback(() => {
    if (!scrollBoxRef.current) return;
    const container = scrollBoxRef.current;
    const containerTop = container.getBoundingClientRect().top;

    const cells = Array.from(
      container.querySelectorAll<HTMLElement>(
        '.fc-daygrid-day[data-date$="-01"]'
      )
    );

    let dateStr: string | null = null;
    for (const cell of cells) {
      if (cell.getBoundingClientRect().top <= containerTop + 1) {
        dateStr = cell.getAttribute('data-date');
      } else {
        break;
      }
    }
    if (!dateStr) dateStr = cells[0]?.getAttribute('data-date') ?? null;

    if (dateStr) {
      const date = new Date(`${dateStr}T12:00:00`);
      state.setMonthName(
        new Intl.DateTimeFormat(calendarLocale, {
          month: 'long',
          year: 'numeric'
        }).format(date)
      );
    }
  }, [calendarLocale, state.setMonthName]);

  const monthDayCellClassNames = useCallback(
    (arg: DayCellContentArg): string[] => {
      const monthClass =
        arg.date.getMonth() % 2 === 0
          ? 'fc-day-month-even'
          : 'fc-day-month-odd';
      const existing = calendarProps.dayCellClassNames;
      if (!existing) return [monthClass];
      if (typeof existing === 'function') {
        const result = existing(arg);
        const arr = Array.isArray(result) ? result : result ? [result] : [];
        return [monthClass, ...arr];
      }
      if (Array.isArray(existing)) return [monthClass, ...existing];
      return [monthClass, existing as string];
    },
    [calendarProps.dayCellClassNames]
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
              <SearchInput searchCallback={state.setSearchTerm} />
            )}
            {enableRefresh && (
              <ActionIcon
                variant='transparent'
                aria-label='calendar-refresh'
                disabled={isLoading}
                onClick={() => state.query.refetch()}
              >
                <Tooltip label={t`Refresh calendar`} position='top-end'>
                  <IconRefresh />
                </Tooltip>
              </ActionIcon>
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
                <Tooltip label={t`Export data`} position='top-end'>
                  <IconDownload onClick={state.exportModal.open} />
                </Tooltip>
              </ActionIcon>
            )}
          </Group>
        </Group>
        <Box
          ref={scrollBoxRef}
          pos='relative'
          onScroll={isScrollView ? updateMonthFromScroll : undefined}
          {...(isScrollView && {
            style: {
              height: 'calc(100vh - 160px)',
              overflowY: 'scroll',
              scrollbarGutter: 'stable',
              paddingRight: '12px'
            }
          })}
        >
          <LoadingOverlay visible={state.query.isFetching} />
          <FullCalendar
            ref={state.ref}
            plugins={[dayGridPlugin, interactionPlugin]}
            initialView={isScrollView ? 'scrollMultiMonth' : 'dayGridMonth'}
            {...(isScrollView && {
              views: {
                scrollMultiMonth: {
                  type: 'dayGrid',
                  duration: { months: horizonMonths }
                }
              },
              height: 'auto'
            })}
            locales={allLocales}
            locale={calendarLocale}
            firstDay={Number.parseInt(
              globalSettings.getSetting('WEEK_STARTS_ON') ?? '1',
              10
            )}
            headerToolbar={false}
            footerToolbar={false}
            {...calendarProps}
            datesSet={datesSet}
            eventContent={wrappedEventContent}
            dayCellClassNames={
              isScrollView
                ? monthDayCellClassNames
                : calendarProps.dayCellClassNames
            }
          />
        </Box>
      </Stack>
    </>
  );
}
