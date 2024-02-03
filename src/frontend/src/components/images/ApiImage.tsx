/**
 * Component for loading an image from the InvenTree server using the CSRF cookie
 *
 * Image caching is handled automagically by the browsers cache
 */
import { Image, ImageProps, Skeleton, Stack } from '@mantine/core';
import { useId } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { api } from '../../App';

/**
 * Construct an image container which will load and display the image
 */
export function ApiImage(props: ImageProps) {
  const [image, setImage] = useState<string>('');

  const [authorized, setAuthorized] = useState<boolean>(true);

  const queryKey = useId();

  const _imgQuery = useQuery({
    queryKey: ['image', queryKey, props.src],
    enabled:
      authorized &&
      props.src != undefined &&
      props.src != null &&
      props.src != '',
    queryFn: async () => {
      if (!props.src) {
        return null;
      }
      return api
        .get(props.src, {
          responseType: 'blob'
        })
        .then((response) => {
          switch (response.status) {
            case 200:
              let img = new Blob([response.data], {
                type: response.headers['content-type']
              });
              let url = URL.createObjectURL(img);
              setImage(url);
              break;
            default:
              // User is not authorized to view this image, or the image is not available
              setImage('');
              setAuthorized(false);
              break;
          }

          return response;
        })
        .catch((_error) => {
          return null;
        });
    },
    refetchOnMount: true,
    refetchOnWindowFocus: false
  });

  return (
    <Stack>
      {image && image.length > 0 ? (
        <Image {...props} src={image} withPlaceholder fit="contain" />
      ) : (
        <Skeleton
          height={props?.height ?? props.width}
          width={props?.width ?? props.height}
        />
      )}
    </Stack>
  );
}
