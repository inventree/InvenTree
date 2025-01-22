import type { DatesSetArg } from '@fullcalendar/core';
import { t } from '@lingui/macro';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { useState } from 'react';
import { api } from '../../App';
import Calendar from '../../components/calendar/Calendar';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { showApiErrorMessage } from '../../functions/notifications';
import { apiUrl } from '../../states/ApiState';

export default function BuildCalendar() {
  const [minDate, setMinDate] = useState<Date | null>(null);
  const [maxDate, setMaxDate] = useState<Date | null>(null);

  const onDatesChange = (dateInfo: DatesSetArg) => {
    if (!!dateInfo.start) {
      setMinDate(dayjs(dateInfo.start).subtract(1, 'month').toDate());
    }

    if (!!dateInfo.end) {
      setMaxDate(dayjs(dateInfo.end).add(1, 'month').toDate());
    }
  };

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

  return <Calendar events={[]} datesSet={onDatesChange} />;
}
