import { Group } from '@mantine/core';

import { ApiPaths } from '../../states/ApiState';
import { GeneralRenderer } from './GeneralRenderer';
import { PartRenderer } from './PartRenderer';

export const StockItemRenderer = ({ pk }: { pk: string }) => {
  const DetailRenderer = (data: any) => {
    return (
      <Group position="apart">
        {data?.quantity}
        <small>
          <PartRenderer pk={data?.part_detail.pk} data={data?.part_detail} />
        </small>
      </Group>
    );
  };
  return (
    <GeneralRenderer
      api_key={ApiPaths.stock_item_list}
      api_ref="stockitem"
      link={`/stock/item/${pk}`}
      pk={pk}
      renderer={DetailRenderer}
    />
  );
};
