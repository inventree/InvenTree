import type { IconProps } from '@tabler/icons-react';

export type TablerIconType = React.ForwardRefExoticComponent<
  Omit<IconProps, 'ref'> & React.RefAttributes<SVGSVGElement>
>;

export type InvenTreeIconType = {
  [key: string]: TablerIconType;
};
