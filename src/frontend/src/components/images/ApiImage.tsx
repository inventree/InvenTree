/**
 * Component for loading an image from the InvenTree server
 *
 * Image caching is handled automagically by the browsers cache
 */
import { Image, type ImageProps, Skeleton, Stack } from '@mantine/core';
import { useEffect, useMemo, useRef, useState } from 'react';

import { generateUrl } from '../../functions/urls';
import { useLocalState } from '../../states/LocalState';

interface ApiImageProps extends ImageProps {
  onClick?: (event: any) => void;
  thumbnail?: string;
}

/**
 * Construct an image container which will load and display the image
 */
export function ApiImage(props: Readonly<ApiImageProps>) {
  const { getHost } = useLocalState.getState();

  const [isLoaded, setIsLoaded] = useState<boolean>(false);
  const highResRef = useRef<HTMLImageElement>(null);

  const imageUrl = useMemo(() => {
    return generateUrl(props.src, getHost());
  }, [getHost, props.src]);

  const thumbnailUrl = useMemo(() => {
    if (props.thumbnail) {
      return generateUrl(props.thumbnail, getHost());
    } else {
      return null;
    }
  }, [getHost, props.thumbnail]);

  // Hook for progressive loading of the high-res image
  useEffect(() => {
    setIsLoaded(false);

    const img = new window.Image();
    img.src = imageUrl;
    img.onload = () => setIsLoaded(true);

    return () => {
      img.onload = null;
    };
  }, [imageUrl]);

  return (
    <Stack>
      {thumbnailUrl && !isLoaded && (
        <Image
          {...props}
          src={thumbnailUrl}
          fit='contain'
          style={{
            position: 'absolute',
            filter: 'blur(1px)',
            transform: 'scale(0.95)',
            opacity: isLoaded ? 0 : 1,
            transition: 'opacity 0.2s ease'
          }}
        />
      )}
      {imageUrl ? (
        <Image
          ref={highResRef}
          {...props}
          src={imageUrl}
          fit='contain'
          style={{
            ...props.style,
            opacity: isLoaded ? 1 : 0,
            transition: 'opacity 0.2s ease'
          }}
        />
      ) : (
        <Skeleton h={props?.h ?? props.w} w={props?.w ?? props.h} />
      )}
    </Stack>
  );
}
