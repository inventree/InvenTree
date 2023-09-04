import { Anchor, Loader } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';

import { api } from '../../App';
import { ApiPaths, url } from '../../states/ApiState';
import { ThumbnailHoverCard } from '../items/Thumbnail';

export function GeneralRenderer({
  api_key,
  api_ref: ref,
  link,
  pk,
  renderer
}: {
  api_key: ApiPaths;
  api_ref: string;
  link: string;
  pk: string;
  renderer?: (data: any) => JSX.Element;
}) {
  const { data, isError, isFetching, isLoading } = useQuery({
    queryKey: [ref, pk],
    queryFn: () => {
      return api.get(url(api_key, pk)).then((res) => res.data);
    }
  });

  if (isError) {
    return <div>Something went wrong...</div>;
  }

  if (isFetching || isLoading) {
    return <Loader />;
  }

  if (renderer) {
    if (link) {
      return (
        <Anchor href={link} style={{ textDecoration: 'none' }}>
          {renderer(data)}
        </Anchor>
      );
    }
    return renderer(data);
  }
  return (
    <ThumbnailHoverCard
      src={data.thumbnail || data.image}
      text={data.name}
      link={link}
    />
  );
}
