import { Center, Loader, MantineProvider, Stack } from '@mantine/core';
import {
  type ComponentType,
  type JSX,
  Suspense,
  useEffect,
  useState
} from 'react';

import { colorSchema } from '../contexts/colorSchema';
import { theme } from '../theme';

function LoadingFallback({
  fullHeight = false
}: { fullHeight: boolean }): JSX.Element {
  return (
    <MantineProvider theme={theme} colorSchemeManager={colorSchema}>
      <Stack h={fullHeight ? '100vh' : undefined}>
        <Center h={fullHeight ? '100vh' : undefined}>
          <Loader />
        </Center>
      </Stack>
    </MantineProvider>
  );
}

export function Loadable(
  Component: any,
  noFallback = false,
  fullHeight = false
): any {
  return (props: JSX.IntrinsicAttributes) => (
    <Suspense
      fallback={
        !noFallback ? <LoadingFallback fullHeight={fullHeight} /> : undefined
      }
    >
      <Component {...props} />
    </Suspense>
  );
}

export function LoadingItem({ item }: Readonly<{ item: any }>): JSX.Element {
  const Itm = Loadable(item);
  return <Itm />;
}

/**
 * Like Loadable, but never suspends: the import is resolved into plain
 * state instead of thrown as a Suspense promise, so React.lazy's commit-
 * delay heuristic never kicks in (it can otherwise hold the first render -
 * and everything below it - back by several hundred ms even once the chunk
 * is cached).
 *
 * The import itself is NOT started at module-load: some chunks evaluate
 * top-level i18n macros, which throws if that happens before the active
 * locale is set. It starts on mount (same as React.lazy would), or earlier
 * via the returned component's `.preload()`, which callers can invoke once
 * they know it's safe to (e.g. once the locale is ready).
 *
 * Only use this for components that are needed on (or immediately after)
 * initial load; for genuinely route-specific pages, prefer Loadable/lazy so
 * the chunk isn't fetched until it's needed.
 */
export function EagerLoadable(
  importFn: () => Promise<{ default: ComponentType<any> }>
): ComponentType<any> & { preload: () => Promise<ComponentType<any>> } {
  let componentPromise: Promise<ComponentType<any>> | null = null;

  function preload() {
    if (!componentPromise) {
      componentPromise = importFn().then((m) => m.default);
    }
    return componentPromise;
  }

  function EagerLoaded(props: JSX.IntrinsicAttributes) {
    const [Component, setComponent] = useState<ComponentType<any> | null>(null);

    useEffect(() => {
      let cancelled = false;
      preload().then((C) => {
        if (!cancelled) setComponent(() => C);
      });
      return () => {
        cancelled = true;
      };
    }, []);

    if (!Component) {
      return null;
    }

    return <Component {...props} />;
  }

  EagerLoaded.preload = preload;
  return EagerLoaded;
}
