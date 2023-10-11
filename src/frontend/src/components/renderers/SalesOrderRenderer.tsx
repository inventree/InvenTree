import { ApiPaths } from '../../states/ApiState';
import { GeneralRenderer } from './GeneralRenderer';

export const SalesOrderRenderer = ({ pk }: { pk: string }) => {
  return (
    <GeneralRenderer
      api_key={ApiPaths.sales_order_list}
      api_ref="sales_order"
      link={`/order/so/${pk}`}
      pk={pk}
      renderer={(data: any) => {
        return data.reference;
      }}
    />
  );
};
