import { ApiPaths } from '../../states/ApiState';
import { GeneralRenderer } from './GeneralRenderer';

export const PartRenderer = ({ pk }: { pk: string }) => {
  return (
    <GeneralRenderer
      api_key={ApiPaths.part_detail}
      api_ref="part"
      link={`/part/${pk}`}
      pk={pk}
    />
  );
};
