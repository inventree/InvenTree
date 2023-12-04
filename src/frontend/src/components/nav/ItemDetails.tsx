import { Paper } from '@mantine/core';

import { DetailsImage } from '../images/DetailsImage';
import { Thumbnail } from '../images/Thumbnail';

function defineFields(part: any) {
  return [
    {
      accessor: 'image',
      type: 'image'
    }
  ];
}

export function ItemDetails({ params = {} }: { params?: any }) {
  console.log(params);
  const fields = defineFields(params);

  return (
    <Paper withBorder={true}>
      <DetailsImage src={params.image} />
    </Paper>
  );
}
