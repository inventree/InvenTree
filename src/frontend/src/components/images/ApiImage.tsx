/**
 * Component for loading an image from the InvenTree server
 *
 * Image caching is handled automagically by the browsers cache
 */
import { Image, type ImageProps, Skeleton, Stack } from '@mantine/core';
import { useMemo } from 'react';

import { generateUrl } from '../../functions/urls';
import { useLocalState } from '../../states/LocalState';

interface ApiImageProps extends ImageProps {
  onClick?: (event: any) => void;
}

/**
 * Construct an image container which will load and display the image
 */
export function ApiImage(props: Readonly<ApiImageProps>) {
  const { host } = useLocalState.getState();

  const imageUrl = useMemo(() => {
    return generateUrl(props.src, host);
  }, [host, props.src]);

  return (
    <Stack>
      {imageUrl ? (
        <Image {...props} src={imageUrl} fit='contain' />
      ) : (
        <Skeleton h={props?.h ?? props.w} w={props?.w ?? props.h} />
      )}
    </Stack>
  );
}
