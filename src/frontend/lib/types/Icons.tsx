import type { Icon, IconProps } from '@tabler/icons-react';

export type TablerIconType = React.ForwardRefExoticComponent<
  Omit<IconProps, 'ref'> & React.RefAttributes<Icon>
>;

export type InvenTreeIconType = {
  [key: string]: TablerIconType;
};
