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
import type { ModelType } from '../../enums/ModelType';
import type { UserRoles } from '../../enums/Roles';
import { navigateToLink } from '../../functions/navigation';
import { getDetailUrl } from '../../functions/urls';
import useCalendar from '../../hooks/UseCalendar';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { ModelInformationDict } from '../render/ModelType';
import Calendar from './Calendar';

/**
 * A generic calendar component for displaying orders
 * This can be used for the following order types:
 * - BuildOrder
 * - PurchaseOrder
 * - SalesOrder
 * - ReturnOrder
 */

export default function OrderCalendar({
  model,
  role,
  params
}: {
  model: ModelType;
  role: UserRoles;
  params: Record<string, any>;
}) {
  const navigate = useNavigate();
  const user = useUserState();

  const modelInfo = useMemo(() => {
    return ModelInformationDict[model];
  }, [model]);

  const canEdit = useMemo(() => {
    return user.hasChangeRole(role);
  }, [user, role]);

  const calendarState = useCalendar({
    endpoint: modelInfo.api_endpoint,
    name: model.toString(),
    queryParams: params
  });

  // Build the events
  const events = useMemo(() => {
    const today = dayjs().toISOString().split('T')[0];

    return (
      calendarState.data?.map((order: any) => {
        const start: string =
          order.start_date || order.issue_date || order.creation_date || today;
        const end: string = order.target_date || start;

        return {
          id: order.pk,
          title: order.reference,
          description: order.description,
          start: start,
          end: end,
          startEditable: canEdit && !!order.start_date,
          durationEditable: canEdit
        };
      }) ?? []
    );
  }, [calendarState.data, canEdit]);

  // Callback when Order is edited
  const onEditOrder = (info: EventChangeArg) => {
    const orderId = info.event.id;
    const patch: Record<string, string> = {};

    if (info.event.start && info.event.start != info.oldEvent.start) {
      patch.start_date = info.event.start.toISOString().split('T')[0];
    }

    if (info.event.end && info.event.end != info.oldEvent.end) {
      patch.target_date = info.event.end.toISOString().split('T')[0];
    }

    if (!!patch) {
      api
        .patch(apiUrl(modelInfo.api_endpoint, orderId), patch)
        .then(() => {
          hideNotification('calendar-edit-result');
          showNotification({
            id: 'calendar-edit-result',
            message: t`Order Updated`,
            color: 'green'
          });
        })
        .catch(() => {
          info.revert();
          hideNotification('calendar-edit-result');
          showNotification({
            id: 'calendar-edit-result',
            message: t`Error updating order`,
            color: 'red'
          });
        });
    }
  };

  // Callback when PurchaseOrder is clicked
  const onClickOrder = (info: EventClickArg) => {
    if (!!info.event.id) {
      navigateToLink(
        getDetailUrl(model, info.event.id),
        navigate,
        info.jsEvent
      );
    }
  };

  const renderOrder = useCallback(
    (event: EventContentArg) => {
      const order = calendarState.data?.find(
        (order: any) => order.pk.toString() == event.event.id.toString()
      );

      if (!order) {
        // Fallback to the event title if no order is found
        return event.event.title;
      }

      return (
        <Group gap='xs' wrap='nowrap'>
          {order.overdue && (
            <ActionIcon
              color='orange-7'
              variant='transparent'
              title={t`Overdue`}
            >
              <IconCalendarExclamation />
            </ActionIcon>
          )}
          <Text size='sm' fw={700}>
            {order.reference}
          </Text>
          <Text size='xs'>{order.description ?? order.title}</Text>
        </Group>
      );
    },
    [calendarState.data]
  );

  return (
    <Calendar
      enableDownload
      enableSearch
      events={events}
      state={calendarState}
      editable={true}
      eventContent={renderOrder}
      eventClick={onClickOrder}
      eventChange={onEditOrder}
    />
  );
}
