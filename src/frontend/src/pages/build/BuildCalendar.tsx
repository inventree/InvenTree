import type {
  DatesSetArg,
  EventClickArg,
  EventContentArg
} from '@fullcalendar/core';
import { t } from '@lingui/macro';
import { ActionIcon, Group, Text } from '@mantine/core';
import { IconCalendarExclamation } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../App';
import Calendar from '../../components/calendar/Calendar';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { navigateToLink } from '../../functions/navigation';
import { showApiErrorMessage } from '../../functions/notifications';
import { getDetailUrl } from '../../functions/urls';
import { apiUrl } from '../../states/ApiState';

export default function BuildCalendar() {
  const navigate = useNavigate();

  const [minDate, setMinDate] = useState<Date | null>(null);
  const [maxDate, setMaxDate] = useState<Date | null>(null);

  const buildQuery = useQuery({
    enabled: !!minDate && !!maxDate,
    queryKey: ['builds', minDate, maxDate],
    queryFn: async () =>
      api
        .get(apiUrl(ApiEndpoints.build_order_list), {
          params: {
            outstanding: true,
            min_date: minDate?.toISOString().split('T')[0],
            max_date: maxDate?.toISOString().split('T')[0]
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
        })
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

  // Callback when data range changes
  const onDatesChange = (dateInfo: DatesSetArg) => {
    if (!!dateInfo.start) {
      setMinDate(dayjs(dateInfo.start).subtract(1, 'month').toDate());
    }

    if (!!dateInfo.end) {
      setMaxDate(dayjs(dateInfo.end).add(1, 'month').toDate());
    }
  };

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
      eventContent={renderBuildOrder}
      datesSet={onDatesChange}
      eventClick={onEventClick}
    />
  );
}
