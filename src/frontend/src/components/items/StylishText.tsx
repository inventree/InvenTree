import { InvenTreeStylishText } from '@lib/components/InvenTreeStylishText';
import {
  type MantineSize,
  type MantineTheme,
  useMantineTheme
} from '@mantine/core';
import type { JSX } from 'react';

export default function StylishText({
  children,
  size
}: Readonly<{
  children: JSX.Element | string;
  size?: MantineSize;
}>) {
  const theme: MantineTheme = useMantineTheme();

  return (
    <InvenTreeStylishText theme={theme} size={size}>
      {children}
    </InvenTreeStylishText>
  );
}
