import { ApiPaths } from '../../states/ApiState';
import { GeneralRenderer } from './GeneralRenderer';

export const StockLocationRenderer = ({ pk }: { pk: string }) => {
  return (
    <GeneralRenderer
      api_key={ApiPaths.stock_location_list}
      api_ref="stock_location"
      link={`/stock/location/${pk}`}
      pk={pk}
      image={false}
    />
  );
};
