import type { CalendarOptions } from '@fullcalendar/core';
import allLocales from '@fullcalendar/core/locales-all';
import dayGridPlugin from '@fullcalendar/daygrid';
import FullCalendar from '@fullcalendar/react';
import { useLocalState } from '../../states/LocalState';

export default function Calendar(props: CalendarOptions) {
  const [locale] = useLocalState((s) => [s.language]);

  return (
    <FullCalendar
      plugins={[dayGridPlugin]}
      initialView='dayGridMonth'
      locales={allLocales}
      locale={locale}
      {...props}
    />
  );
}
