import { Anchor, type AnchorProps } from '@mantine/core';
import { IconLink } from '@tabler/icons-react';
import type { ReactNode } from 'react';
import { cancelEvent } from './Events';

// Only these URL protocols are permitted for rendered links
const ALLOWED_LINK_PROTOCOLS: string[] = ['http:', 'https:'];

/**
 * Validate a user-supplied URL for use as an external link.
 *
 * - The URL must be absolute and parseable
 * - Only http and https protocols are permitted
 *   (this rejects e.g. javascript:, data:, vbscript:, file: URLs)
 *
 * @param url - The URL to validate
 * @returns The normalized URL string if valid, otherwise null
 */
export function sanitizeLinkUrl(url: any): string | null {
  if (typeof url !== 'string') {
    return null;
  }

  const value = url.trim();

  if (!value) {
    return null;
  }

  try {
    const parsed = new URL(value);

    if (!ALLOWED_LINK_PROTOCOLS.includes(parsed.protocol.toLowerCase())) {
      return null;
    }

    return parsed.href;
  } catch {
    return null;
  }
}

export type RenderLinkOptions = {
  /** Icon size (default = 18) */
  size?: number;
  /** Optional content to render instead of the link icon */
  children?: ReactNode;
  /** Content to render if the URL is empty (default = '-') */
  placeholder?: ReactNode;
  /** Additional props passed through to the Anchor component */
  anchorProps?: AnchorProps;
};

/**
 * Render an external link as an <Anchor> element with a link icon.
 *
 * The URL is validated before rendering - only absolute http / https URLs
 * are rendered as clickable links. Invalid or unsafe URLs are rendered
 * as plain (escaped) text, so that the value is still visible to the user.
 *
 * Links are opened in a new tab, with "noopener" and "noreferrer" set.
 *
 * @param url - The URL to render
 * @param options - Optional rendering options
 */
export function renderLink(
  url: string | null | undefined,
  options: RenderLinkOptions = {}
): ReactNode {
  const placeholder = options.placeholder ?? '-';

  if (!url || (typeof url === 'string' && !url.trim())) {
    return placeholder;
  }

  const href = sanitizeLinkUrl(url);

  if (!href) {
    // Not a valid / permitted URL - render as plain text (React escapes this)
    return String(url);
  }

  return (
    <Anchor
      {...options.anchorProps}
      href={href}
      target='_blank'
      rel='noreferrer noopener'
      title={href}
      onClick={(event: any) => {
        cancelEvent(event);
        window.open(href, '_blank', 'noopener,noreferrer');
      }}
    >
      {options.children ?? <IconLink size={options.size ?? 18} />}
    </Anchor>
  );
}
