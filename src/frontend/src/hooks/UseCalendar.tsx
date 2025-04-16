import type FullCalendar from '@fullcalendar/react';
import type { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { FilterSetState } from '@lib/types/Filters';
import type { UseModalReturn } from '@lib/types/Modals';
import type { DateValue } from '@mantine/dates';
import { type UseQueryResult, useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { useCallback, useMemo, useRef, useState } from 'react';
import { api } from '../App';
import { showApiErrorMessage } from '../functions/notifications';
import useDataExport from './UseDataExport';
import { useFilterSet } from './UseFilterSet';

/*
 * Type definition for representing the state of a calendar:
 *
 * ref: A reference to the FullCalendar component
 * filterSet: The current filter set state
 * monthName: The name of the current month (e.g. "January 2022")
 * setMonthName: A function to set the month name
 * searchTerm: The current search term for the calendar
 * setSearchTerm: A function to set the search term
 * startDate: The start date of the current date range
 * setStartDate: A function to set the start date
 * endDate: The end date of the current date range
 * setEndDate: A function to set the end date
 * nextMonth: A function to navigate to the next month
 * prevMonth: A function to navigate to the previous month
 * currentMonth: A function to navigate to the current month
 * selectMonth: A function to select a specific month
 */
export type CalendarState = {
  name: string;
  ref: React.RefObject<FullCalendar>;
  filterSet: FilterSetState;
  monthName: string;
  setMonthName: (name: string) => void;
  searchTerm: string;
  startDate: Date | null;
  setStartDate: (date: Date | null) => void;
  endDate: Date | null;
  setEndDate: (date: Date | null) => void;
  setSearchTerm: (term: string) => void;
  nextMonth: () => void;
  prevMonth: () => void;
  currentMonth: () => void;
  selectMonth: (date: DateValue) => void;
  query: UseQueryResult;
  exportModal: UseModalReturn;
  data: any;
};

export default function useCalendar({
  name,
  endpoint,
  queryParams
}: {
  name: string;
  endpoint: ApiEndpoints;
  queryParams?: any;
}): CalendarState {
  const ref = useRef<FullCalendar>(null as any);

  const filterSet = useFilterSet(`calendar-${name}`);

  const [searchTerm, setSearchTerm] = useState<string>('');

  const [monthName, setMonthName] = useState<string>('');

  const [startDate, setStartDate] = useState<Date | null>(null);

  const [endDate, setEndDate] = useState<Date | null>(null);

  // Generate a set of API query filters
  const queryFilters: Record<string, any> = useMemo(() => {
    // Expand date range by one month, to ensure we capture all events

    let params = {
      ...(queryParams || {})
    };

    if (filterSet.activeFilters) {
      filterSet.activeFilters.forEach((filter) => {
        params[filter.name] = filter.value;
      });
    }

    params = {
      ...params,
      min_date: startDate
        ? dayjs(startDate).subtract(1, 'month').format('YYYY-MM-DD')
        : null,
      max_date: endDate
        ? dayjs(endDate).add(1, 'month').format('YYYY-MM-DD')
        : null,
      search: searchTerm
    };

    return params;
  }, [startDate, endDate, searchTerm, filterSet.activeFilters, queryParams]);

  const query = useQuery({
    enabled: !!startDate && !!endDate,
    queryKey: ['calendar', name, endpoint, queryFilters],
    queryFn: async () => {
      // Fetch data from the API
      return api
        .get(apiUrl(endpoint), {
          params: queryFilters
        })
        .then((response) => {
          return response.data ?? [];
        })
        .catch((error) => {
          showApiErrorMessage({
            error: error,
            title: 'Error fetching calendar data'
          });
        });
    }
  });

  // Navigate to the previous month
  const prevMonth = useCallback(() => {
    ref.current?.getApi().prev();
  }, [ref]);

  // Navigate to the next month
  const nextMonth = useCallback(() => {
    ref.current?.getApi().next();
  }, [ref]);

  // Navigate to the current month
  const currentMonth = useCallback(() => {
    ref.current?.getApi().today();
  }, [ref]);

  // Callback to select a specific month from a picker
  const selectMonth = useCallback(
    (date: DateValue) => {
      if (date && ref?.current) {
        const api = ref.current.getApi();

        api.gotoDate(date);
      }
    },
    [ref]
  );

  // Modal for exporting data from the calendar
  const exportModal = useDataExport({
    url: apiUrl(endpoint),
    enabled: true,
    filters: queryFilters
  });

  return {
    name,
    filterSet,
    ref,
    monthName,
    setMonthName,
    searchTerm,
    setSearchTerm,
    nextMonth,
    prevMonth,
    currentMonth,
    selectMonth,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    exportModal,
    query: query,
    data: query.data
  };
}
