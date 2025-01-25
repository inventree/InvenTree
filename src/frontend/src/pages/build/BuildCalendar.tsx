import type { EventClickArg, EventContentArg } from '@fullcalendar/core';
import { t } from '@lingui/macro';
import { ActionIcon, Group, Text } from '@mantine/core';
import { IconCalendarExclamation } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../App';
import Calendar from '../../components/calendar/Calendar';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { navigateToLink } from '../../functions/navigation';
import { showApiErrorMessage } from '../../functions/notifications';
import { getDetailUrl } from '../../functions/urls';
import useCalendar from '../../hooks/UseCalendar';
import { apiUrl } from '../../states/ApiState';

export default function BuildCalendar() {
  const navigate = useNavigate();

  const calendarState = useCalendar('buildorder-index');

  const buildQuery = useQuery({
    enabled: !!calendarState.startDate && !!calendarState.endDate,
    queryKey: [
      'builds',
      calendarState.startDate,
      calendarState.endDate,
      calendarState.searchTerm
    ],
    queryFn: async () => {
      // Expand the
      const min_date = dayjs(calendarState.startDate).subtract(1, 'month');
      const max_date = dayjs(calendarState.endDate).add(1, 'month');

      return api
        .get(apiUrl(ApiEndpoints.build_order_list), {
          params: {
            part_detail: true,
            outstanding: true,
            min_date: min_date?.toISOString().split('T')[0],
            max_date: max_date?.toISOString().split('T')[0],
            search: calendarState.searchTerm
          }
        })
        .then((response) => {
          return response.data ?? [];
        })
        .catch((error) => {
          showApiErrorMessage({
            error: error,
            title: t`Error fetching build orders`
          });
        });
    }
  });

  // Build the calendar events
  const events = useMemo(() => {
    const today = dayjs().toISOString().split('T')[0];

    return (
      buildQuery.data?.map((build: any) => {
        const start: string = build.start_date || today;
        const end: string = build.target_date || build.start_date || today;

        const inProgress =
          dayjs(start).isBefore(today) && dayjs(end).isAfter(today);
        const overdue = dayjs(end).isBefore(today);

        const color: string = overdue
          ? 'var(--mantine-color-orange-7)'
          : inProgress
            ? 'var(--mantine-color-green-3)'
            : 'var(--mantine-color-blue-3)';

        return {
          id: build.pk,
          title: build.reference,
          description: build.title,
          start: start,
          end: end,
          backgroundColor: color
        };
      }) ?? []
    );
  }, [buildQuery.data]);

  // Callback when a build is clicked on
  const onEventClick = (info: EventClickArg) => {
    if (!!info.event.id) {
      navigateToLink(
        getDetailUrl(ModelType.build, info.event.id),
        navigate,
        info.jsEvent
      );
    }
  };

  const renderBuildOrder = useCallback(
    (event: EventContentArg) => {
      // Find the matching build order
      const build = buildQuery.data?.find(
        (b: any) => b.pk.toString() == event.event.id.toString()
      );

      if (!build) {
        // Fallback to the title if no description is available
        return event.event.title;
      }

      return (
        <Group gap='xs' wrap='nowrap'>
          {build.overdue && (
            <ActionIcon
              color='orange-7'
              variant='transparent'
              title={t`Overdue`}
              size='xs'
            >
              <IconCalendarExclamation />
            </ActionIcon>
          )}
          <Text size='sm' fw={700}>
            {build.reference}
          </Text>
          <Text size='xs'>{build.title}</Text>
        </Group>
      );
    },
    [buildQuery.data]
  );

  return (
    <Calendar
      events={events}
      state={calendarState}
      isLoading={buildQuery.isFetching}
      eventContent={renderBuildOrder}
      eventClick={onEventClick}
    />
  );
}
