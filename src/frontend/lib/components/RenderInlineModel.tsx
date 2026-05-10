import { getBaseUrl, navigateToLink, shortenString } from '@lib/index';
import {
  Anchor,
  Group,
  type MantineSize,
  Paper,
  Space,
  Text
} from '@mantine/core';
import { type ReactNode, useCallback } from 'react';
import { Thumbnail } from './images/Thumbnail';

/**
 * Helper function for rendering an inline model in a consistent style
 */

export function RenderInlineModel({
  primary,
  secondary,
  prefix,
  suffix,
  image,
  labels,
  url,
  navigate,
  showSecondary = true,
  tooltip
}: Readonly<{
  primary: ReactNode;
  secondary?: ReactNode;
  showSecondary?: boolean;
  prefix?: ReactNode;
  suffix?: ReactNode;
  image?: string;
  labels?: string[];
  url?: string;
  navigate?: any;
  tooltip?: string;
}>): ReactNode {
  // TODO: Handle labels
  const onClick = useCallback(
    (event: any) => {
      if (url && navigate) {
        navigateToLink(url, navigate, event);
      }
    },
    [url, navigate]
  );

  if (typeof primary === 'string') {
    primary = shortenString({
      str: primary,
      len: 50
    });

    primary = <Text size='sm'>{primary}</Text>;
  }

  if (typeof secondary === 'string') {
    secondary = shortenString({
      str: secondary,
      len: 75
    });

    if (secondary.toString()?.length > 0) {
      secondary = <InlineSecondaryBadge text={secondary.toString()} />;
    }
  }

  if (typeof suffix === 'string') {
    suffix = <Text size='xs'>{suffix}</Text>;
  }

  return (
    <Group gap='xs' justify='space-between' title={tooltip}>
      <Group gap='xs' justify='left'>
        {prefix}
        {image && <Thumbnail src={image} size={18} />}
        {url ? (
          <Anchor
            href={`/${getBaseUrl()}${url}`}
            onClick={(event: any) => onClick(event)}
          >
            {primary}
          </Anchor>
        ) : (
          primary
        )}
        {showSecondary && secondary && secondary}
      </Group>
      {suffix && (
        <>
          <Space />
          {suffix}
        </>
      )}
    </Group>
  );
} /**
 * Render a "badge like" component with a text label
 */

export function InlineSecondaryBadge({
  text,
  title,
  size = 'xs'
}: {
  text: string;
  title?: string;
  size?: MantineSize;
}): ReactNode {
  return (
    <Paper p={2} withBorder style={{ backgroundColor: 'transparent' }}>
      <Group gap='xs' wrap='nowrap'>
        {title && (
          <Text size={size} title={title}>
            {title}:
          </Text>
        )}
        <Text size={size ?? 'xs'}>{text}</Text>
      </Group>
    </Paper>
  );
}
