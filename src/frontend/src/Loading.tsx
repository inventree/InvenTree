import { Center, Loader, Stack } from '@mantine/core';
import { Suspense, lazy } from 'react';

export function Loading() {
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
    <Suspense fallback={<Loading />}>
      <Component {...props} />
    </Suspense>
  );
