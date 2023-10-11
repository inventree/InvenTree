import { Group } from '@mantine/core';

import { ApiPaths } from '../../states/ApiState';
import { GeneralRenderer } from './GeneralRenderer';
import { PartRenderer } from './PartRenderer';

export const SupplierPartRenderer = ({ pk }: { pk: string }) => {
  const DetailRenderer = (data: any) => {
    return (
      <Group position="apart">
        {data?.SKU}
        <small>
          <span style={{ color: 'white' }}>
            <PartRenderer
              pk={data?.part_detail?.pk}
              data={data?.part_detail}
              link={false}
            />
          </span>
        </small>
      </Group>
    );
  };
  return (
    <GeneralRenderer
      api_key={ApiPaths.supplier_part_list}
      api_ref="supplier_part"
      link={`/supplier-part/${pk}`}
      pk={pk}
      renderer={DetailRenderer}
    />
  );
};
