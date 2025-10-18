import { Center, Loader, MantineProvider, Stack } from '@mantine/core';
import { type JSX, Suspense } from 'react';

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
