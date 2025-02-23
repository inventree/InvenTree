import type {
  EventChangeArg,
  EventClickArg,
  EventContentArg
} from '@fullcalendar/core';
import { t } from '@lingui/macro';
import { ActionIcon, Group, Text } from '@mantine/core';
import { IconCalendarExclamation } from '@tabler/icons-react';
import dayjs from 'dayjs';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import Calendar from '../../components/calendar/Calendar';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { navigateToLink } from '../../functions/navigation';
import { getDetailUrl } from '../../functions/urls';
import useCalendar from '../../hooks/UseCalendar';
import { useUserState } from '../../states/UserState';

export default function PurchaseOrderCalenadar() {
  const navigate = useNavigate();
  const user = useUserState();

  const canEdit = useMemo(() => {
    return user.hasChangeRole(UserRoles.purchase_order);
  }, [user]);

  const calendarState = useCalendar({
    endpoint: ApiEndpoints.purchase_order_list,
    name: 'purchaseorder',
    queryParams: {
      supplier_detail: true,
      outstanding: true
    }
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

  // Callback when PurchaseOrder is edited
  const onEditOrder = (info: EventChangeArg) => {
    // TODO
  };

  // Callback when PurchaseOrder is clicked
  const onClickOrder = (info: EventClickArg) => {
    if (!!info.event.id) {
      navigateToLink(
        getDetailUrl(ModelType.purchaseorder, info.event.id),
        navigate,
        info.jsEvent
      );
    }
  };

  const renderPurchaseOrder = useCallback(
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
          <Text size='xs'>{order.description}</Text>
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
      eventContent={renderPurchaseOrder}
      eventClick={onClickOrder}
      eventChange={onEditOrder}
    />
  );
}
