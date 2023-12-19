import { Paper, Text } from '@mantine/core';

import { DetailsImage } from '../images/DetailsImage';
import { Thumbnail } from '../images/Thumbnail';
import { PartThumbTable } from '../tables/part/PartThumbTable';

const imageActions = {
  selectExisting: true,
  uploadFile: true,
  deleteFile: true
};

export function ItemDetails({
  params = {},
  apiPath,
  refresh = null
}: {
  params?: any;
  apiPath: string;
  refresh: any;
}) {
  return (
    <Paper withBorder={true}>
      <DetailsImage
        imageActions={imageActions}
        src={params.image}
        apiPath={apiPath}
        refresh={refresh}
        pk={params.pk}
      />
    </Paper>
  );
}
