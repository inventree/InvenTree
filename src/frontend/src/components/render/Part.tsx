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
  } else if (stock != null && stock <= 0) {
    badgeColor = 'orange';
    badgeText = t`No stock`;
  } else if (stock != null) {
    badgeText = `${t`Stock`}: ${formatDecimal(stock)}`;
    badgeColor = instance.minimum_stock > stock ? 'yellow' : 'green';
  }

  const badge = !!badgeText ? (
    <Badge size='xs' color={badgeColor}>
      {badgeText}
    </Badge>
  ) : null;

  return (
    <RenderInlineModel
      {...props}
      primary={instance.full_name ?? instance.name}
      secondary={instance.description}
      suffix={badge}
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

/**
 * Inline rendering of a PartParameterTemplate instance
 */
export function RenderPartParameterTemplate({
  instance
}: Readonly<{
  instance: any;
}>): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.name}
      secondary={instance.description}
      suffix={instance.units}
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
