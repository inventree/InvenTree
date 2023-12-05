import { Paper } from '@mantine/core';

import { DetailsImage } from '../images/DetailsImage';

const imageActions = {
  selectExisting: true,
  uploadFile: true,
  deleteFile: true
};

export function ItemDetails({ params = {} }: { params?: any }) {
  return (
    <Paper withBorder={true}>
      <DetailsImage imageActions={imageActions} src={params.image} />
    </Paper>
  );
}
