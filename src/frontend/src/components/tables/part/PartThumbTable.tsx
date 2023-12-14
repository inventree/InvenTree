import { Checkbox, Paper, Radio, SimpleGrid, Text } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { Suspense, useState } from 'react';

import { api } from '../../../App';
import { ApiPaths } from '../../../enums/ApiEndpoints';
import { apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';

export type ThumbTableProps = {
  limit?: number;
  offset?: number;
  search?: string;
};

function PartThumbComponent(props: any) {
  const src = props.element?.image
    ? `/media/${props.element?.image}`
    : undefined;
  return (
    <Paper key={props.index}>
      <Checkbox
        label={
          <Paper>
            <Thumbnail size={120} src={src}></Thumbnail>
            <Text>
              {props.element.image.split('/')[1]} ({props.element.count})
            </Text>
          </Paper>
        }
        value={props.index}
      />
    </Paper>
  );
}

export function PartThumbTable({
  limit = 25,
  offset = 0,
  search = ''
}: ThumbTableProps) {
  const [selected, setSelected] = useState(0);

  const q = useQuery({
    queryKey: [
      apiUrl(ApiPaths.part_thumbs_list),
      { limit: limit, offset: offset, search: search }
    ],
    queryFn: async () => {
      return api.get(apiUrl(ApiPaths.part_thumbs_list), {
        params: {
          offset: offset,
          limit: limit,
          search: search
        }
      });
    }
  });

  return (
    <Suspense>
      <SimpleGrid cols={5}>
        {q.data?.data.map((data: any, index: number) => (
          <PartThumbComponent element={data} key={index} checked={selected} />
        ))}
      </SimpleGrid>
    </Suspense>
  );
}
