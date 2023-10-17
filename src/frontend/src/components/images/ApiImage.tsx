/**
 * Component for loading an image from the InvenTree server,
 * using the API's token authentication.
 *
 * Image caching is handled automagically by the browsers cache
 */
import {
  Image,
  ImageProps,
  LoadingOverlay,
  Overlay,
  Stack
} from '@mantine/core';
import { useId } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { api } from '../../App';

/**
 * Construct an image container which will load and display the image
 */
export function ApiImage(props: ImageProps) {
  const [image, setImage] = useState<string>('');

  const queryKey = useId();

  const imgQuery = useQuery({
    queryKey: ['image', queryKey, props.src],
    enabled: props.src != undefined && props.src != null && props.src != '',
    queryFn: async () => {
      if (!props.src) {
        return null;
      }
      return api
        .get(props.src, {
          responseType: 'blob'
        })
        .then((response) => {
          let img = new Blob([response.data], {
            type: response.headers['content-type']
          });
          let url = URL.createObjectURL(img);
          setImage(url);
          return response;
        })
        .catch((error) => {
          console.error(`Error fetching image ${props.src}:`, error);
          return null;
        });
    },
    refetchOnMount: true,
    refetchOnWindowFocus: false
  });

  return (
    <Stack>
      <LoadingOverlay visible={imgQuery.isLoading || imgQuery.isFetching} />
      <Image {...props} src={image} />
      {imgQuery.isError && <Overlay color="#F00" />}
    </Stack>
  );
}
