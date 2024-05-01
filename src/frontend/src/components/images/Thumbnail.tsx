import { t } from '@lingui/macro';
import { Anchor, Group, Skeleton, Text } from '@mantine/core';
import { ReactNode, useMemo } from 'react';

import { ApiImage } from './ApiImage';

/*
 * Render an image, loaded via the API
 */
export function Thumbnail({
  src,
  alt = t`Thumbnail`,
  size = 20,
  link,
  text,
  align
}: {
  src?: string | undefined;
  alt?: string;
  size?: number;
  text?: ReactNode;
  align?: string;
  link?: string;
}) {
  const backup_image = '/static/img/blank_image.png';

  const inner = useMemo(() => {
    if (link) {
      return (
        <Anchor href={link} target="_blank">
          {text}
        </Anchor>
      );
    } else {
      return text;
    }
  }, [link, text]);

  return (
    <Group align={align ?? 'left'} gap="xs" wrap="nowrap">
      <ApiImage
        src={src || backup_image}
        aria-label={alt}
        w={size}
        fit="contain"
        radius="xs"
        style={{ maxHeight: size }}
      />
      {inner}
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
      <Group justify="left" gap={10} wrap="nowrap">
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
