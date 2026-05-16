import type { ReactNode } from 'react';

/**
 * Type used to specify a single panel in a panel group
 */
export type PanelType = {
  name: string;
  label: string;
  controls?: ReactNode;
  icon?: ReactNode;
  indicator?: boolean | (() => Promise<boolean>);
  content?: ReactNode;
  hidden?: boolean;
  disabled?: boolean;
  showHeadline?: boolean;
  supportsDirty?: boolean;
};

export type PanelGroupType = {
  id: string;
  label: string;
  panelIDs?: string[];
  panels?: PanelType[];
};
