import { Group } from '@mantine/core';

import { ApiPaths } from '../../states/ApiState';
import { GeneralRenderer } from './GeneralRenderer';
import { PartRenderer } from './PartRenderer';

export const BuildOrderRenderer = ({ pk }: { pk: string }) => {
  const DetailRenderer = (data: any) => {
    return (
      <Group position="apart">
        {data?.reference}
        <small>
          <PartRenderer
            pk={data?.part_detail?.pk}
            data={data?.part_detail}
            link={true}
          />
        </small>
      </Group>
    );
  };
  return (
    <GeneralRenderer
      api_key={ApiPaths.build_order_list}
      api_ref="build_order"
      link={`/build/${pk}`}
      pk={pk}
      renderer={DetailRenderer}
    />
  );
};
