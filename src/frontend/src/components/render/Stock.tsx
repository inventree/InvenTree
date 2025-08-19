import { t } from '@lingui/core/macro';
import { Group, Text } from '@mantine/core';
import type { ReactNode } from 'react';

import { ModelType } from '@lib/enums/ModelType';
import { formatDecimal } from '@lib/functions/Formatting';
import { getDetailUrl } from '@lib/functions/Navigation';
import { shortenString } from '../../functions/tables';
import { TableHoverCard } from '../../tables/TableHoverCard';
import { ApiIcon } from '../items/ApiIcon';
import {
  InlineSecondaryBadge,
  type InstanceRenderInterface,
  RenderInlineModel
} from './Instance';

/**
 * Inline rendering of a single StockLocation instance
 */
export function RenderStockLocation(
  props: Readonly<InstanceRenderInterface>
): ReactNode {
  const { instance } = props;

  if (!instance) {
    return '';
  }

  const suffix: ReactNode = (
    <Group gap='xs'>
      <TableHoverCard
        value={<Text size='sm'>{instance.description}</Text>}
        position='bottom-end'
        zIndex={10000}
        icon='sitemap'
        title={t`Location`}
        extra={[<Text>{instance.pathstring}</Text>]}
      />
    </Group>
  );

  const location = shortenString({
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
      primary={location}
      suffix={suffix}
      url={
        props.link
          ? getDetailUrl(ModelType.stocklocation, instance.pk)
          : undefined
      }
    />
  );
}

/**
 * Inline rendering of a single StockLocationType instance
 */
export function RenderStockLocationType({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return (
    <RenderInlineModel
      primary={instance.name}
      prefix={instance.icon && <ApiIcon name={instance.icon} />}
      secondary={`${instance.description} (${instance.location_count})`}
    />
  );
}

export function RenderStockItem(
  props: Readonly<InstanceRenderInterface>
): ReactNode {
  const { instance } = props;
  let quantity_string = '';

  const allocated: number = Math.max(0, instance?.allocated ?? 0);

  if (instance?.serial !== null && instance?.serial !== undefined) {
    quantity_string += `${t`Serial Number`}: ${instance.serial}`;
  } else if (allocated > 0) {
    const available: number = Math.max(0, instance.quantity - allocated);
    quantity_string = `${t`Available`}: ${formatDecimal(available)} / ${formatDecimal(instance.quantity)}`;
  } else if (instance?.quantity) {
    quantity_string = `${t`Quantity`}: ${formatDecimal(instance.quantity)}`;
  }

  const showLocation: boolean = props.extra?.show_location !== false;
  const location: any = props.instance?.location_detail;

  // Form the "secondary" text to display
  const secondary: ReactNode = (
    <Group gap='xs' style={{ paddingLeft: '5px' }}>
      {showLocation && location?.name && (
        <InlineSecondaryBadge title={t`Location`} text={location.name} />
      )}
      {instance.batch && (
        <InlineSecondaryBadge title={t`Batch`} text={instance.batch} />
      )}
    </Group>
  );

  // Form the "suffix" text to display
  const suffix: ReactNode = (
    <Group gap='xs' wrap='nowrap'>
      <Text size='xs'>{quantity_string}</Text>
      {location && (
        <TableHoverCard
          value=''
          position='bottom-end'
          zIndex={10000}
          icon='sitemap'
          title={t`Location`}
          extra={[<Text>{location.pathstring}</Text>]}
        />
      )}
    </Group>
  );

  return (
    <RenderInlineModel
      {...props}
      primary={instance.part_detail?.full_name}
      secondary={secondary}
      suffix={suffix}
      image={instance.part_detail?.thumbnail || instance.part_detail?.image}
      url={
        props.link ? getDetailUrl(ModelType.stockitem, instance.pk) : undefined
      }
    />
  );
}
