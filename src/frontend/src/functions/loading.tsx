import { Center, Loader, Stack } from '@mantine/core';
import { Suspense } from 'react';

function LoadingFallback() {
  return (
    <Stack>
      <Center>
        <Loader />
      </Center>
    </Stack>
  );
}

export const Loadable = (Component: any) => (props: JSX.IntrinsicAttributes) =>
  (
    <Suspense fallback={<LoadingFallback />}>
      <Component {...props} />
    </Suspense>
  );

export function LoadingItem({ item }: { item: any }): JSX.Element {
  const Itm = Loadable(item);
  return <Itm />;
}
