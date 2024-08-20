import { t } from '@lingui/macro';
import { ReactNode } from 'react';

import { ModelType } from '../../enums/ModelType';
import { getDetailUrl } from '../../functions/urls';
import { ApiIcon } from '../items/ApiIcon';
import { InstanceRenderInterface, RenderInlineModel } from './Instance';

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
          <div style={{ width: 10 * (instance.level || 0) }}></div>
          {instance.icon && <ApiIcon name={instance.icon} />}
        </>
      }
      primary={instance.name}
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
      secondary={instance.description + ` (${instance.location_count})`}
    />
  );
}

export function RenderStockItem(
  props: Readonly<InstanceRenderInterface>
): ReactNode {
  const { instance } = props;
  let quantity_string = '';

  if (instance?.serial !== null && instance?.serial !== undefined) {
    quantity_string += t`Serial Number` + `: ${instance.serial}`;
  } else if (instance?.quantity) {
    quantity_string = t`Quantity` + `: ${instance.quantity}`;
  }

  return (
    <RenderInlineModel
      {...props}
      primary={instance.part_detail?.full_name}
      suffix={quantity_string}
      image={instance.part_detail?.thumbnail || instance.part_detail?.image}
      url={
        props.link ? getDetailUrl(ModelType.stockitem, instance.pk) : undefined
      }
    />
  );
}
