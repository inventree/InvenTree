import {
  type MantineSize,
  Text,
  darken,
  getThemeColor,
  lighten,
  useMantineColorScheme,
  useMantineTheme
} from '@mantine/core';
import { useMemo } from 'react';
import { useLocalState } from '../../states/LocalState';

// A stylish text component that uses the primary color of the theme
export function StylishText({
  children,
  size
}: Readonly<{
  children: JSX.Element | string;
  size?: MantineSize;
}>) {
  const { usertheme } = useLocalState();
  const theme = useMantineTheme();
  const colorScheme = useMantineColorScheme();

  const primary = useMemo(() => {
    return getThemeColor(usertheme.primaryColor, theme);
  }, [usertheme.primaryColor, theme]);

  const secondary = useMemo(() => {
    let secondary = primary;
    if (colorScheme.colorScheme == 'dark') {
      secondary = lighten(primary, 0.3);
    } else {
      secondary = darken(primary, 0.3);
    }

    return secondary;
  }, [usertheme, colorScheme, primary]);

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
