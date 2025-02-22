import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import type { ReactNode } from 'react';

import { ModelType } from '../../enums/ModelType';
import { getDetailUrl } from '../../functions/urls';
import { ApiIcon } from '../items/ApiIcon';
import { type InstanceRenderInterface, RenderInlineModel } from './Instance';

/**
 * Inline rendering of a single StockLocation instance
 */
export function RenderStockLocation(
  props: Readonly<InstanceRenderInterface>
): ReactNode {
  const { instance } = props;

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
      primary={instance.pathstring}
      secondary={instance.description}
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

  if (instance?.serial !== null && instance?.serial !== undefined) {
    quantity_string += `${t`Serial Number`}: ${instance.serial}`;
  } else if (instance?.quantity) {
    quantity_string = `${t`Quantity`}: ${instance.quantity}`;
  }

  let batch_string = '';

  if (!!instance.batch) {
    batch_string = `${t`Batch`}: ${instance.batch}`;
  }

  return (
    <RenderInlineModel
      {...props}
      primary={instance.part_detail?.full_name}
      secondary={batch_string}
      suffix={<Text size='xs'>{quantity_string}</Text>}
      image={instance.part_detail?.thumbnail || instance.part_detail?.image}
      url={
        props.link ? getDetailUrl(ModelType.stockitem, instance.pk) : undefined
      }
    />
  );
}
