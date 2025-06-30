import { t } from '@lingui/core/macro';
import { Anchor, Group, HoverCard, Image } from '@mantine/core';
import { type ReactNode, useMemo } from 'react';

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
  align,
  hover,
  hoverSize = 128
}: Readonly<{
  src?: string;
  alt?: string;
  size?: number;
  text?: ReactNode;
  align?: string;
  link?: string;
  hover?: boolean;
  hoverSize?: number;
}>) {
  const backup_image = '/static/img/blank_image.png';

  const inner = useMemo(() => {
    if (link) {
      return (
        <Anchor href={link} target='_blank'>
          {text}
        </Anchor>
      );
    } else {
      return text;
    }
  }, [link, text]);

  return (
    <HoverCard
      disabled={!hover}
      withinPortal
      position='left'
      shadow='xs'
      closeDelay={100}
    >
      <HoverCard.Target>
        <Group align={align ?? 'left'} gap='xs' wrap='nowrap'>
          <ApiImage
            src={src || backup_image}
            aria-label={alt}
            w={size}
            fit='contain'
            radius='xs'
            style={{ maxHeight: size }}
          />
          {inner}
        </Group>
      </HoverCard.Target>
      <HoverCard.Dropdown>
        <Image
          src={src || backup_image}
          alt={alt}
          w={hoverSize}
          fit='contain'
          style={{ maxHeight: hoverSize }}
        />
      </HoverCard.Dropdown>
    </HoverCard>
  );
}
