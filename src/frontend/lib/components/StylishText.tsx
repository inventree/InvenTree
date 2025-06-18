import {
  type MantineSize,
  Text,
  darken,
  getThemeColor,
  useMantineTheme
} from '@mantine/core';
import { useMemo } from 'react';
import type { JSX } from 'react';

// Hook that memoizes the gradient color based on the primary color of the theme
const useThematicGradient = () => {
  const theme = useMantineTheme();

  const primary = useMemo(() => {
    return getThemeColor(theme.primaryColor, theme);
  }, [theme]);

  const secondary = useMemo(() => darken(primary, 0.9), [primary]);

  return useMemo(() => {
    return { primary, secondary };
  }, [primary, secondary]);
};

// A stylish text component that uses the primary color of the theme
export function StylishText({
  children,
  size
}: Readonly<{
  children: JSX.Element | string;
  size?: MantineSize;
}>) {
  const { primary, secondary } = useThematicGradient();

  return (
    <Text
      fw={700}
      size={size ?? 'xl'}
      variant='gradient'
      gradient={{ from: primary.toString(), to: secondary.toString() }}
    >
      {children}
    </Text>
  );
}
