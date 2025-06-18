import {
  type MantineSize,
  type MantineTheme,
  Text,
  darken,
  getThemeColor
} from '@mantine/core';
import { useMemo } from 'react';
import type { JSX } from 'react';

// Hook that memoizes the gradient color based on the primary color of the theme
const useThematicGradient = ({
  suppliedTheme
}: {
  suppliedTheme: MantineTheme;
}) => {
  const primary = useMemo(() => {
    return getThemeColor(suppliedTheme.primaryColor, suppliedTheme);
  }, [suppliedTheme]);

  const secondary = useMemo(() => darken(primary, 0.25), [primary]);

  return useMemo(() => {
    return { primary, secondary };
  }, [primary, secondary]);
};

/**
 * A stylish text component that uses the primary color of the theme
 * Note that the "theme" object must be provided by the parent component.
 * - For plugins this theme object is provided.
 * - For the main UI, we have a separate <StylishText> component
 */
export function InvenTreeStylishText({
  children,
  theme,
  size
}: Readonly<{
  children: JSX.Element | string;
  theme: MantineTheme;
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
