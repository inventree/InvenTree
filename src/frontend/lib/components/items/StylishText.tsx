import { Text } from '@mantine/core';

export function StylishText({
  children,
  size = 'md'
}: Readonly<{
  children: JSX.Element | string;
  size?: string;
}>) {
  return (
    <Text size={size} variant='gradient'>
      {children}
    </Text>
  );
}
