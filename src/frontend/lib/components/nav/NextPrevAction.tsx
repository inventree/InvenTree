import { ActionIcon, Group, Tooltip } from '@mantine/core';
import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react';
import type { ReactNode } from 'react';

import { t } from '@lingui/core/macro';

/**
 * Minimal description of a single prev/next navigation target.
 *
 * The caller is responsible for resolving the actual destination URL /
 * primary key. The component never decides what "next" means on its own,
 * because the meaning depends on the model, filter set, and ordering
 * policy of the calling list view.
 */
export interface NextPrevTarget {
  /** Optional visible label for the destination (e.g. "Widget A") */
  label?: string;
  /** Primary key of the destination instance */
  pk?: number | string | null;
  /**
   * Called when the user clicks the button. Should be a no-op if `pk`
   * is undefined/null; the component already disables the button in
   * that case.
   */
  onClick?: () => void;
  /**
   * Set to true while the destination is being resolved. Disables the
   * button and shows a muted tooltip.
   */
  loading?: boolean;
  /**
   * Override the default tooltip text (English fallback).
   * Localized messages should be supplied by the caller.
   */
  tooltip?: string;
}

export interface NextPrevActionProps {
  /** Configuration for the "previous" button. Omit / leave undefined to hide it. */
  prev?: NextPrevTarget;
  /** Configuration for the "next" button. Omit / leave undefined to hide it. */
  next?: NextPrevTarget;
  /**
   * Allow callers (e.g. detail pages) to provide localized tooltip
   * messages keyed by 'prev' / 'next'. Falls back to the English default.
   */
  labels?: {
    prev?: ReactNode;
    next?: ReactNode;
    prevAria?: string;
    nextAria?: string;
  };
  /** Optional size override for both icons (default 'sm') */
  size?: string;
}

/**
 * Returns true when the target is usable (has either a pk or an onClick).
 */
function hasTarget(target?: NextPrevTarget): boolean {
  if (!target) return false;
  if (target.pk === undefined || target.pk === null) {
    return Boolean(target.onClick);
  }
  return true;
}

/**
 * Render a "previous / next" navigation pair as compact action icons.
 *
 * This component is intentionally dumb: it does not know how to find the
 * adjacent instance. The caller must supply `pk` (and/or `onClick`) for
 * each side, typically by querying the API with the same filter / ordering
 * parameters as the originating list.
 *
 * The component is exported through the `lib` surface so frontend plugins
 * can reuse it for any entity detail view, matching the requirement set
 * out in https://github.com/inventree/InvenTree/issues/12397.
 */
export function NextPrevAction({
  prev,
  next,
  labels,
  size = 'sm'
}: Readonly<NextPrevActionProps>) {
  const showPrev = hasTarget(prev);
  const showNext = hasTarget(next);

  if (!showPrev && !showNext) {
    return null;
  }

  const prevTooltip = labels?.prev ?? prev?.tooltip ?? t`Previous item`;

  const nextTooltip = labels?.next ?? next?.tooltip ?? t`Next item`;

  const prevDisabled = !prev?.onClick || prev.loading === true;
  const nextDisabled = !next?.onClick || next.loading === true;

  return (
    <Group gap={2} wrap='nowrap' data-testid='inventree-next-prev-action'>
      {showPrev && (
        <Tooltip
          label={prevTooltip}
          withinPortal
          disabled={prevDisabled}
          position='bottom'
        >
          <ActionIcon
            variant='subtle'
            size={size}
            color='blue'
            radius='sm'
            aria-label={labels?.prevAria ?? 'previous-item'}
            data-testid='inventree-prev-item'
            disabled={prevDisabled}
            onClick={() => prev?.onClick?.()}
          >
            <IconChevronLeft />
          </ActionIcon>
        </Tooltip>
      )}
      {showNext && (
        <Tooltip
          label={nextTooltip}
          withinPortal
          disabled={nextDisabled}
          position='bottom'
        >
          <ActionIcon
            variant='subtle'
            size={size}
            color='blue'
            radius='sm'
            aria-label={labels?.nextAria ?? 'next-item'}
            data-testid='inventree-next-item'
            disabled={nextDisabled}
            onClick={() => next?.onClick?.()}
          >
            <IconChevronRight />
          </ActionIcon>
        </Tooltip>
      )}
    </Group>
  );
}
