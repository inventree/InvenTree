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
  extraEntries,
  modelType
}: {
  event: EventContentArg;
  prefix?: string | React.ReactNode;
  instanceLookup: string;
  extraEntries?: { label: string; value: string | React.ReactNode }[];
  modelType: ModelType;
}) {
  // Extract the order instance from the event
  const order = event?.event?._def?.extendedProps?.order;

  const instance = resolveItem(order, instanceLookup);

  if (!order) return null;

  const entries = extraEntries || [];

  if (order.project_code_detail?.code) {
    entries.push({
      label: t`Project Code`,
      value: order.project_code_detail.code
    });
  }

  return (
    <Stack gap='xs' style={{ minWidth: 250 }}>
      <RenderInstance model={modelType} instance={instance} />
      <Divider />
      <Group grow gap='xs' justify='space-between'>
        <Text size='sm' fw='bold'>
          {order.reference}
        </Text>
        <Text size='xs'>{order.description || order.title}</Text>
      </Group>
      {entries.map((entry, index) => (
        <Group key={index} grow gap='xs' justify='space-between'>
          <Text size='sm' fw='bold'>
            {entry.label}
          </Text>
          <Text size='xs'>{entry.value}</Text>
        </Group>
      ))}
      {order.start_date && (
        <Group grow gap='xs' justify='space-between'>
          <Text size='sm' fw='bold'>{t`Start Date`}</Text>
          <Text size='xs'>{formatDate(order.start_date)}</Text>
        </Group>
      )}
      {order.target_date && (
        <Group grow gap='xs' justify='space-between'>
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
        <Group grow gap='xs' justify='space-between'>
          <Text size='sm' fw='bold'>{t`Responsible`}</Text>
          <RenderOwner instance={order.responsible_detail} />
        </Group>
      )}
    </Stack>
  );
}
