import { Text, useMantineTheme } from '@mantine/core';

export function StylishText({
  children,
  size = 'md'
}: Readonly<{
  children: JSX.Element | string;
  size?: string;
}>) {
  const theme = useMantineTheme();

  return (
    <Text size={size} className={classes.signText} c={theme.primaryColor}>
      {children}
    </Text>
  );
}
