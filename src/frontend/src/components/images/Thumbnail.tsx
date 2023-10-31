import { t } from '@lingui/macro';
import { Anchor } from '@mantine/core';
import { Group } from '@mantine/core';
import { Text } from '@mantine/core';
import { useMemo } from 'react';

import { ApiImage } from './ApiImage';

export function Thumbnail({
  src,
  alt = t`Thumbnail`,
  size = 20
}: {
  src?: string | undefined;
  alt?: string;
  size?: number;
}) {
  // TODO: Use HoverCard to display a larger version of the image

  return (
    <ApiImage
      src={src || '/static/img/blank_image.png'}
      alt={alt}
      width={size}
      fit="contain"
      radius="xs"
      withPlaceholder
      imageProps={{
        style: {
          maxHeight: size
        }
      }}
    />
  );
}

export function ThumbnailHoverCard({
  src,
  text,
  link = '',
  alt = t`Thumbnail`,
  size = 24
}: {
  src: string;
  text: string;
  link?: string;
  alt?: string;
  size?: number;
}) {
  const card = useMemo(() => {
    return (
      <Group position="left" spacing={10} noWrap={true}>
        <Thumbnail src={src} alt={alt} size={size} />
        <Text>{text}</Text>
      </Group>
    );
  }, [src, text, alt, size]);

  if (link)
    return (
      <Anchor href={link} style={{ textDecoration: 'none' }}>
        {card}
      </Anchor>
    );

  return <div>{card}</div>;
}
