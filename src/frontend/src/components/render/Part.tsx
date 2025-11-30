import { t } from '@lingui/core/macro';
import { Badge, Group, Text } from '@mantine/core';
import type { ReactNode } from 'react';

import { ModelType } from '@lib/enums/ModelType';
import { formatDecimal } from '@lib/functions/Formatting';
import { getDetailUrl } from '@lib/functions/Navigation';
import { shortenString } from '../../functions/tables';
import { TableHoverCard } from '../../tables/TableHoverCard';
import { ApiIcon } from '../items/ApiIcon';
import { type InstanceRenderInterface, RenderInlineModel } from './Instance';

/**
 * Inline rendering of a single Part instance
 */
export function RenderPart(
  props: Readonly<InstanceRenderInterface>
): ReactNode {
  const { instance } = props;

  let badgeText = '';
  let badgeColor = '';

  const stock: number | null = instance.total_in_stock ?? null;

  if (instance.active == false) {
    badgeColor = 'red';
    badgeText = t`Inactive`;
  } else if (instance.virtual) {
    badgeColor = 'blue';
    badgeText = t`Virtual`;
  } else if (stock != null && stock <= 0) {
    badgeColor = 'orange';
    badgeText = t`No stock`;
  } else if (stock != null) {
    badgeText = `${t`Stock`}: ${formatDecimal(stock)}`;
    badgeColor = instance.minimum_stock > stock ? 'yellow' : 'green';
  }

  const extra: ReactNode[] = [];

  // For active parts, we can display some extra information here
  if (instance.active) {
    if (instance.ordering) {
      extra.push(
        <Text size='xs'>
          {t`On Order`}: {formatDecimal(instance.ordering)}{' '}
        </Text>
      );
    }

    if (instance.building) {
      extra.push(
        <Text size='xs'>
          {t`In Production`}: {formatDecimal(instance.building)}{' '}
        </Text>
      );
    }
  }

  const suffix: ReactNode = (
    <Group gap='xs' wrap='nowrap'>
      {badgeText && (
        <Badge size='xs' color={badgeColor}>
          {badgeText}
        </Badge>
      )}
      {extra && (
        <TableHoverCard
          value=''
          position='bottom-end'
          zIndex={10000}
          icon='info'
          title={t`Details`}
          extra={extra}
        />
      )}
    </Group>
  );

  return (
    <RenderInlineModel
      {...props}
      primary={instance.full_name ?? instance.name}
      secondary={instance.description}
      suffix={suffix}
      image={instance.thumbnail || instance.image}
      url={props.link ? getDetailUrl(ModelType.part, instance.pk) : undefined}
    />
  );
}

/**
 * Inline rendering of a PartCategory instance
 */
export function RenderPartCategory(
  props: Readonly<InstanceRenderInterface>
): ReactNode {
  const { instance } = props;

  if (!instance) {
    return '';
  }

  const suffix: ReactNode = (
    <Group gap='xs'>
      <TableHoverCard
        value={<Text size='xs'>{instance.description}</Text>}
        position='bottom-end'
        zIndex={10000}
        icon='sitemap'
        title={t`Category`}
        extra={[<Text>{instance.pathstring}</Text>]}
      />
    </Group>
  );

  const category = shortenString({
    str: instance.pathstring,
    len: 50
  });

  return (
    <RenderInlineModel
      {...props}
      tooltip={instance.pathstring}
      prefix={
        <>
          {instance.level > 0 && `${'- '.repeat(instance.level)}`}
          {instance.icon && <ApiIcon name={instance.icon} />}
        </>
      }
      primary={category}
      suffix={suffix}
      url={
        props.link
          ? getDetailUrl(ModelType.partcategory, instance.pk)
          : undefined
      }
    />
  );
}

export function RenderPartTestTemplate({
  instance
}: Readonly<{
  instance: any;
}>): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.test_name}
      suffix={instance.description}
    />
  );
}
