import { ActionIcon, Group, Tooltip } from '@mantine/core';
import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react';
import {
  type MouseEvent,
  type ReactNode,
  useCallback,
  useEffect,
  useMemo
} from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { ModelInformationDict } from '../enums/ModelInformation';
import {
  eventModified,
  getDetailUrl,
  navigateToLink
} from '../functions/Navigation';
import type { DetailNavigationContext } from '../types/Navigation';

const DEFAULT_FOCUS_STORAGE_KEY = 'inventree-detail-navigation-focus';

export type DetailNavigationTarget = {
  url: string;
  label?: ReactNode;
  tooltip?: string;
  state?: unknown;
  disabled?: boolean;
};

export type DetailNavigationProps = {
  previous?: DetailNavigationTarget;
  next?: DetailNavigationTarget;
  focusStorageKey?: string;
};

type StoredFocus = {
  id?: string;
  name?: string;
};

function getContext(locationState: unknown): DetailNavigationContext | null {
  const context = (locationState as { detailNavigation?: unknown } | null)
    ?.detailNavigation;

  if (!context || typeof context !== 'object') {
    return null;
  }

  const value = context as Partial<DetailNavigationContext>;
  const modelInfo = value.modelType
    ? ModelInformationDict[value.modelType]
    : undefined;

  if (
    !modelInfo ||
    !Array.isArray(value.ids) ||
    value.ids.length < 2 ||
    typeof value.index !== 'number' ||
    value.index < 0 ||
    value.index >= value.ids.length
  ) {
    return null;
  }

  return {
    modelType: value.modelType!,
    ids: value.ids,
    index: value.index
  };
}

function useContextNavigation(): DetailNavigationProps | undefined {
  const location = useLocation();

  return useMemo(() => {
    const context = getContext(location.state);

    if (!context) {
      return undefined;
    }

    const target = (index: number): DetailNavigationTarget | undefined => {
      const id = context.ids[index];
      const url = getDetailUrl(context.modelType, id);

      if (!url) {
        return undefined;
      }

      return {
        url,
        state: {
          detailNavigation: {
            ...context,
            index
          }
        }
      };
    };

    return {
      previous: context.index > 0 ? target(context.index - 1) : undefined,
      next:
        context.index < context.ids.length - 1
          ? target(context.index + 1)
          : undefined
    };
  }, [location.state]);
}

function readStoredFocus(storageKey: string): StoredFocus | null {
  try {
    const value = window.sessionStorage.getItem(storageKey);

    if (!value) {
      return null;
    }

    const focus = JSON.parse(value) as StoredFocus;

    if (!focus || (!focus.id && !focus.name)) {
      return null;
    }

    return focus;
  } catch {
    return null;
  }
}

function restoreStoredFocus(storageKey: string) {
  const focus = readStoredFocus(storageKey);

  if (!focus) {
    return;
  }

  const target = focus.id
    ? document.getElementById(focus.id)
    : focus.name
      ? Array.from(document.getElementsByName(focus.name)).find(
          (element): element is HTMLElement => element instanceof HTMLElement
        )
      : undefined;

  if (target) {
    target.focus({ preventScroll: true });
    window.sessionStorage.removeItem(storageKey);
  }
}

function rememberActiveFocus(storageKey: string) {
  const active = document.activeElement;

  if (!(active instanceof HTMLElement) || active === document.body) {
    return;
  }

  const id = active.id || undefined;
  const name = active.getAttribute('name') || undefined;

  if (!id && !name) {
    return;
  }

  try {
    window.sessionStorage.setItem(storageKey, JSON.stringify({ id, name }));
  } catch {
    // Focus restoration is a progressive enhancement. Ignore storage errors.
  }
}

function NavigationButton({
  target,
  direction,
  focusStorageKey
}: Readonly<{
  target: DetailNavigationTarget;
  direction: 'previous' | 'next';
  focusStorageKey: string;
}>) {
  const navigate = useNavigate();
  const label = target.tooltip ?? target.label ?? direction;
  const Icon = direction === 'previous' ? IconChevronLeft : IconChevronRight;

  const onClick = useCallback(
    (event: MouseEvent<HTMLButtonElement>) => {
      if (!eventModified(event)) {
        rememberActiveFocus(focusStorageKey);
      }

      navigateToLink(target.url, navigate, event, {
        state: target.state
      });
    },
    [focusStorageKey, navigate, target.state, target.url]
  );

  return (
    <Tooltip label={label} position='bottom'>
      <ActionIcon
        aria-label={
          direction === 'previous'
            ? 'detail-navigation-previous'
            : 'detail-navigation-next'
        }
        disabled={target.disabled}
        onClick={onClick}
        variant='subtle'
      >
        <Icon size={18} />
      </ActionIcon>
    </Tooltip>
  );
}

/**
 * Render previous/next controls for a detail page.
 *
 * A table can provide navigation automatically by placing a
 * `detailNavigation` context in React Router state. Plugins may instead pass
 * explicit targets, so no backend-specific table assumptions are required.
 */
export function DetailNavigation({
  previous,
  next,
  focusStorageKey = DEFAULT_FOCUS_STORAGE_KEY
}: Readonly<DetailNavigationProps>) {
  const location = useLocation();
  const contextNavigation = useContextNavigation();
  const navigation = previous || next ? { previous, next } : contextNavigation;

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      restoreStoredFocus(focusStorageKey);
    });

    return () => window.cancelAnimationFrame(frame);
  }, [focusStorageKey, location.key]);

  if (!navigation?.previous && !navigation?.next) {
    return null;
  }

  return (
    <Group gap={0} wrap='nowrap' aria-label='detail-navigation'>
      {navigation.previous && (
        <NavigationButton
          target={navigation.previous}
          direction='previous'
          focusStorageKey={focusStorageKey}
        />
      )}
      {navigation.next && (
        <NavigationButton
          target={navigation.next}
          direction='next'
          focusStorageKey={focusStorageKey}
        />
      )}
    </Group>
  );
}
