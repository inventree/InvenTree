import { Group } from '@mantine/core';

import { ApiPaths } from '../../states/ApiState';
import { GeneralRenderer } from './GeneralRenderer';

export const PurchaseOrderRenderer = ({ pk }: { pk: string }) => {
  const DetailRenderer = (data: any) => {
    const code = data?.project_code_detail?.code;
    return (
      <Group position="apart">
        <div>{data?.reference}</div>
        {code && <div>({code})</div>}
        {data?.supplier_reference && <div>{data?.supplier_reference}</div>}
      </Group>
    );
  };
  return (
    <GeneralRenderer
      api_key={ApiPaths.purchase_order_list}
      api_ref="pruchaseorder"
      link={`/order/purchase-order/${pk}`}
      pk={pk}
      renderer={DetailRenderer}
    />
  );
};
