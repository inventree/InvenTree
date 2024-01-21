import { Paper } from '@mantine/core';

import { DetailsImage } from '../images/DetailsImage';
import { DetailsTable } from '../tables/Details';

export type DetailField = {
  name: string;
  value: any;
};

export type DetailLeftFields = {
  image: boolean;
  types: boolean[];
  fields: DetailField[];
};

export type DetailFields = {
  left: DetailLeftFields;
  right: DetailField[];
};

const imageActions = {
  selectExisting: true,
  uploadFile: true,
  deleteFile: true
};

export function ItemDetails({
  params = {},
  apiPath,
  refresh,
  fields
}: {
  params?: any;
  apiPath: string;
  refresh: () => void;
  fields: any;
}) {
  return (
    <Paper style={{ display: 'flex', gap: '20px' }}>
      <Paper
        withBorder={true}
        style={{ flexBasis: '50%', display: 'flex', gap: '10px' }}
      >
        <div style={{ flexGrow: '0' }}>
          <DetailsImage
            imageActions={imageActions}
            src={params.image}
            apiPath={apiPath}
            refresh={refresh}
            pk={params.pk}
          />
        </div>
        <div style={{ flexGrow: '1' }}>
          <DetailsTable part={params} fields={fields.left.fields} partIcons />
        </div>
      </Paper>
      <Paper style={{ flexBasis: '50%' }} withBorder>
        <DetailsTable part={params} fields={fields.right} />
      </Paper>
    </Paper>
  );
}
