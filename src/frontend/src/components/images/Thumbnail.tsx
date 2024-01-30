import { t } from '@lingui/macro';
import { Anchor, Skeleton } from '@mantine/core';
import { Group } from '@mantine/core';
import { Text } from '@mantine/core';
import { ReactNode, useMemo } from 'react';

import { ApiImage } from './ApiImage';

/*
 * Render an image, loaded via the API
 */
export function Thumbnail({
  src,
  alt = t`Thumbnail`,
  size = 20,
  text,
  align
}: {
  src?: string | undefined;
  alt?: string;
  size?: number;
  text?: ReactNode;
  align?: string;
}) {
  const backup_image = '/static/img/blank_image.png';

  return (
    <Group align={align ?? 'left'} spacing="xs" noWrap={true}>
      <ApiImage
        src={src || backup_image}
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
      {text}
    </Group>
  );
}

export function ThumbnailHoverCard({
  src,
  text,
  link = '',
  alt = t`Thumbnail`,
  size = 20
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

  if (link) {
    return (
      <Anchor href={link} style={{ textDecoration: 'none' }}>
        {card}
      </Anchor>
    );
  }

  return <div>{card}</div>;
}

export function PartHoverCard({ part }: { part: any }) {
  return part ? (
    <ThumbnailHoverCard
      src={part.thumbnail || part.image}
      text={part.full_name}
      alt={part.description}
      link=""
    />
  ) : (
    <Skeleton />
  );
}
