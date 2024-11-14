import type { ReactNode } from 'react';

/**
 * Type used to specify a single panel in a panel group
 */
export type PanelType = {
  name: string;
  label: string;
  icon?: ReactNode;
  content: ReactNode;
  hidden?: boolean;
  disabled?: boolean;
  showHeadline?: boolean;
};
