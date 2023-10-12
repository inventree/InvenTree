import { Anchor, Loader } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';

import { api } from '../../App';
import { ApiPaths, apiUrl } from '../../states/ApiState';
import { ThumbnailHoverCard } from '../items/Thumbnail';

export function GeneralRenderer({
  api_key,
  api_ref: ref,
  link,
  pk,
  image = true,
  data = undefined,
  renderer
}: {
  api_key: ApiPaths;
  api_ref: string;
  link: string;
  pk: string;
  image?: boolean;
  data?: any;
  renderer?: (data: any) => JSX.Element;
}) {
  // check if data was passed - or fetch it
  if (!data) {
    const {
      data: fetched_data,
      isError,
      isFetching,
      isLoading
    } = useQuery({
      queryKey: [ref, pk],
      queryFn: () => {
        return api
          .get(apiUrl(api_key, pk))
          .then((res) => res.data)
          .catch(() => {
            {
            }
          });
      }
    });

    // Loading section
    if (isError) {
      return <div>Something went wrong...</div>;
    }
    if (isFetching || isLoading) {
      return <Loader />;
    }
    data = fetched_data;
  }

  // Renderers
  let content = undefined;
  // Specific renderer was passed
  if (renderer) content = renderer(data);

  // No image and no content no default renderer
  if (image === false && !content) content = data.name;

  // Wrap in link if link was passed
  if (content && link) {
    content = (
      <Anchor href={link} style={{ textDecoration: 'none' }}>
        {content}
      </Anchor>
    );
  }

  // Return content if it exists, else default
  if (content !== undefined) {
    return content;
  }
  return (
    <ThumbnailHoverCard
      src={data.thumbnail || data.image}
      text={data.name}
      link={link}
    />
  );
}
