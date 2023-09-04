import { Group } from '@mantine/core';

import { ApiPaths } from '../../states/ApiState';
import { GeneralRenderer } from './GeneralRenderer';

export const StockItemRenderer = ({ pk }: { pk: string }) => {
  const DetailRenderer = (data: any) => {
    return (
      <Group position="apart">
        {data?.quantity} <small>{data?.part_detail?.name}</small>
      </Group>
    );
  };
  return (
    <GeneralRenderer
      api_key={ApiPaths.stock_item_detail}
      api_ref="stockitem"
      link={`/stock/item/${pk}`}
      pk={pk}
      renderer={DetailRenderer}
    />
  );
};
