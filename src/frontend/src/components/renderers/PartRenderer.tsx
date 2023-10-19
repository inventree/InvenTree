import { ApiPaths } from '../../states/ApiState';
import { GeneralRenderer } from './GeneralRenderer';

export const PartRenderer = ({
  pk,
  data = undefined,
  link = true
}: {
  pk: string;
  data?: any;
  link?: boolean;
}) => {
  return (
    <GeneralRenderer
      api_key={ApiPaths.part_list}
      api_ref="part"
      link={link ? `/part/${pk}` : ''}
      pk={pk}
      data={data}
    />
  );
};
