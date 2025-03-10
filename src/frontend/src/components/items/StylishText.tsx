import { Text } from '@mantine/core';

import * as classes from '../../main.css';

export function StylishText({
  children,
  size = 'md'
}: Readonly<{
  children: JSX.Element | string;
  size?: string;
}>) {
  return (
    <Text size={size} className={classes.signText} variant='gradient'>
      {children}
    </Text>
  );
}
