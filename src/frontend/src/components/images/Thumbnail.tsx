import { t } from '@lingui/macro';
import { Anchor, Group } from '@mantine/core';
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
  align
}: Readonly<{
  src?: string;
  alt?: string;
  size?: number;
  text?: ReactNode;
  align?: string;
  link?: string;
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
  );
}
