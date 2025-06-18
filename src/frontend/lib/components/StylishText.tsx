import {
  type MantineSize,
  type MantineTheme,
  Text,
  darken,
  getThemeColor,
  useMantineTheme
} from '@mantine/core';
import { useMemo } from 'react';
import type { JSX } from 'react';

// Hook that memoizes the gradient color based on the primary color of the theme
const useThematicGradient = ({
  suppliedTheme
}: {
  suppliedTheme?: MantineTheme;
}) => {
  const theme = useMemo(() => {
    if (suppliedTheme && suppliedTheme != undefined) {
      return suppliedTheme;
    }

    return useMantineTheme();
  }, [suppliedTheme, useMantineTheme]);

  const primary = useMemo(() => {
    return getThemeColor(theme.primaryColor, theme);
  }, [theme]);

  const secondary = useMemo(() => darken(primary, 0.25), [primary]);

  return useMemo(() => {
    return { primary, secondary };
  }, [primary, secondary]);
};

// A stylish text component that uses the primary color of the theme
export function StylishText({
  children,
  theme,
  size
}: Readonly<{
  children: JSX.Element | string;
  theme?: MantineTheme;
  size?: MantineSize;
}>) {
  const { primary, secondary } = useThematicGradient({ suppliedTheme: theme });

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
