import { Center, Loader, MantineProvider, Stack } from '@mantine/core';
import { Suspense } from 'react';

import { colorSchema } from '../contexts/colorSchema';
import { theme } from '../theme';

function LoadingFallback() {
  return (
    <MantineProvider theme={theme} colorSchemeManager={colorSchema}>
      <Stack>
        <Center>
          <Loader />
        </Center>
      </Stack>
    </MantineProvider>
  );
}

export const Loadable =
  (Component: any) => (props: JSX.IntrinsicAttributes) => (
    <Suspense fallback={<LoadingFallback />}>
      <Component {...props} />
    </Suspense>
  );

export function LoadingItem({ item }: Readonly<{ item: any }>): JSX.Element {
  const Itm = Loadable(item);
  return <Itm />;
}
