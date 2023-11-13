import { Text } from '@mantine/core';

import { InvenTreeStyle } from '../../globalStyle';

export function StylishText({
  children,
  size = 'md'
}: {
  children: JSX.Element | string;
  size?: string;
}) {
  const { classes } = InvenTreeStyle();
  return (
    <Text size={size} className={classes.signText} variant="gradient">
      {children}
    </Text>
  );
}
