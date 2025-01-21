import allLocales from '@fullcalendar/core/locales-all';
import dayGridPlugin from '@fullcalendar/daygrid';
import FullCalendar from '@fullcalendar/react';
import { useLocalState } from '../../states/LocalState';

export default function Calendar({
  events
}: {
  events: any[];
}) {
  const [locale] = useLocalState((s) => [s.language]);

  return (
    <FullCalendar
      plugins={[dayGridPlugin]}
      initialView='dayGridMonth'
      events={events}
      locales={allLocales}
      locale={locale}
    />
  );
}
