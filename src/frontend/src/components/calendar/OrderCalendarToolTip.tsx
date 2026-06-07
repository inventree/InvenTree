import type { EventContentArg } from '@fullcalendar/core';
import type { ModelType } from '@lib/enums/ModelType';
import { resolveItem } from '@lib/functions/Conversion';
import { t } from '@lingui/core/macro';
import { Badge, Divider, Group, Stack, Text } from '@mantine/core';
import { formatDate } from '../../defaults/formatters';
import { RenderInstance } from '../render/Instance';
import { RenderOwner } from '../render/User';

export default function OrderCalendarToolTip({
  event,
  instanceLookup,
  modelType
}: {
  event: EventContentArg;
  instanceLookup: string;
  modelType: ModelType;
}) {
  // Extract the order instance from the event
  const order = event?.event?._def?.extendedProps?.order;

  const instance = resolveItem(order, instanceLookup);

  if (!order) return null;

  return (
    <Stack gap='xs'>
      <RenderInstance model={modelType} instance={instance} />
      <Divider />
      <Group gap='xs'>
        <Text size='sm' fw='bold'>
          {order.reference}
        </Text>
        <Text size='xs'>{order.description || order.title}</Text>
      </Group>
      {order.start_date && (
        <Group gap='xs'>
          <Text size='sm' fw='bold'>{t`Start Date`}</Text>
          <Text size='xs'>{formatDate(order.start_date)}</Text>
        </Group>
      )}
      {order.target_date && (
        <Group gap='xs'>
          <Text size='sm' fw='bold'>{t`Target Date`}</Text>
          <Text size='xs'>{formatDate(order.target_date)}</Text>
          {order.overdue && (
            <Badge size='sm' color='red'>
              {t`Overdue`}
            </Badge>
          )}
        </Group>
      )}
      {order.responsible && (
        <Group gap='xs'>
          <Text size='sm' fw='bold'>{t`Responsible`}</Text>
          <RenderOwner instance={order.responsible_detail} />
        </Group>
      )}
    </Stack>
  );
}
