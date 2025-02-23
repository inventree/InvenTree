import type {
  EventChangeArg,
  EventClickArg,
  EventContentArg
} from '@fullcalendar/core';
import { t } from '@lingui/macro';
import { ActionIcon, Group, Text } from '@mantine/core';
import { hideNotification, showNotification } from '@mantine/notifications';
import { IconCalendarExclamation } from '@tabler/icons-react';
import dayjs from 'dayjs';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../App';
import Calendar from '../../components/calendar/Calendar';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { navigateToLink } from '../../functions/navigation';
import { getDetailUrl } from '../../functions/urls';
import useCalendar from '../../hooks/UseCalendar';
import {
  useCategoryFilters,
  useOwnerFilters,
  useProjectCodeFilters,
  useUserFilters
} from '../../hooks/UseFilter';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import {
  AssignedToMeFilter,
  HasProjectCodeFilter,
  OrderStatusFilter,
  OverdueFilter,
  ProjectCodeFilter,
  ResponsibleFilter,
  type TableFilter
} from '../../tables/Filter';

export default function BuildCalendar() {
  const navigate = useNavigate();
  const user = useUserState();

  const canEdit = useMemo(() => {
    return user.hasChangeRole(UserRoles.build);
  }, [user]);

  const calendarState = useCalendar({
    endpoint: ApiEndpoints.build_order_list,
    name: 'build',
    queryParams: {
      part_detail: true,
      outstanding: true
    }
  });

  // Build the calendar events
  const events = useMemo(() => {
    const today = dayjs().toISOString().split('T')[0];

    return (
      calendarState.data?.map((build: any) => {
        const start: string = build.start_date || build.creation_date || today;
        const end: string = build.target_date || start;

        // const inProgress =
        //   dayjs(start).isBefore(today) && dayjs(end).isAfter(today);
        // const overdue = dayjs(end).isBefore(today);

        // const color: string = overdue
        //   ? 'var(--mantine-color-orange-7)'
        //   : inProgress
        //     ? 'var(--mantine-color-green-3)'
        //     : 'var(--mantine-color-blue-3)';

        return {
          id: build.pk,
          title: build.reference,
          description: build.title,
          start: start,
          end: end,
          startEditable: canEdit && !!build.start_date,
          durationEditable: canEdit
          // backgroundColor: color
        };
      }) ?? []
    );
  }, [calendarState.data, canEdit]);

  // Callback when a build is edited
  const onEditBuild = (info: EventChangeArg) => {
    const buildId = info.event.id;

    const patch: Record<string, string> = {};

    if (info.event.start && info.event.start != info.oldEvent.start) {
      patch['start_date'] = info.event.start.toISOString().split('T')[0];
    }

    if (info.event.end && info.event.end != info.oldEvent.end) {
      patch['target_date'] = info.event.end.toISOString().split('T')[0];
    }

    if (!!patch) {
      api
        .patch(apiUrl(ApiEndpoints.build_order_list, buildId), patch)
        .then(() => {
          hideNotification('calendar-edit-success');
          showNotification({
            id: 'calendar-edit-success',
            message: t`Order updated`,
            color: 'green'
          });
        })
        .catch(() => {
          info.revert();
          hideNotification('calendar-edit-error');
          showNotification({
            id: 'calendar-edit-error',
            message: t`Error updating order`,
            color: 'red'
          });
        });
    }
  };

  // Callback when a build is clicked on
  const onClickBuild = (info: EventClickArg) => {
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
      const build = calendarState.data?.find(
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
    [calendarState.data]
  );

  const projectCodeFilters = useProjectCodeFilters();
  const ownerFilters = useOwnerFilters();
  const userFilters = useUserFilters();
  const categoryFilters = useCategoryFilters();

  // TODO: Implement filters available for the calendar
  const calendarFilters: TableFilter[] = useMemo(() => {
    return [
      OrderStatusFilter({ model: ModelType.build }),
      OverdueFilter(),
      AssignedToMeFilter(),
      ProjectCodeFilter({ choices: projectCodeFilters.choices }),
      HasProjectCodeFilter(),
      {
        name: 'issued_by',
        label: t`Issued By`,
        description: t`Filter by user who issued this order`,
        choices: userFilters.choices
      },
      ResponsibleFilter({ choices: ownerFilters.choices }),
      {
        name: 'category',
        label: t`Category`,
        description: t`Filter by part category`,
        choices: categoryFilters.choices
      }
    ];
  }, [
    categoryFilters.choices,
    projectCodeFilters.choices,
    ownerFilters.choices,
    userFilters.choices
  ]);

  return (
    <Calendar
      enableDownload
      enableSearch
      events={events}
      state={calendarState}
      editable={true}
      eventContent={renderBuildOrder}
      eventClick={onClickBuild}
      eventChange={onEditBuild}
    />
  );
}
