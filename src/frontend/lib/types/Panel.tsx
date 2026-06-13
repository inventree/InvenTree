import type { ReactNode } from 'react';

// The type of indicator dot to be shown against a panel
export type PanelIndicatorType = 'info' | 'warning' | 'danger' | null;

/**
 * Type used to specify a single panel in a panel group
 */
export type PanelType = {
  name: string;
  label: string;
  controls?: ReactNode;
  icon?: ReactNode;
  notification_dot?: PanelIndicatorType | (() => Promise<PanelIndicatorType>);
  content?: ReactNode;
  hidden?: boolean;
  disabled?: boolean;
  showHeadline?: boolean;
  supportsDirty?: boolean;
  hotkey?: string;
};

/**
 * Type used to specify a group of panels
 */
export type PanelGroupType = {
  id: string;
  label: string;
  panelIDs?: string[];
  panels?: PanelType[];
};
