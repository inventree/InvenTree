import type { ReactNode } from 'react';
import type { SettingsStateProps } from './Settings';

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
 * Properties passed to a factory function which builds a panel for a generic model feature
 *
 * @param model - The model type (e.g. 'part', or a plugin defined model)
 * @param id - The primary key of the model instance
 * @param instanceInfo - Aggregated counts for the instance (e.g. attachment_count)
 */
export type ModelFeaturePanelProps = {
  model: string;
  id: number;
  instanceInfo: Record<string, number | undefined>;
  userSettings: SettingsStateProps;
  globalSettings: SettingsStateProps;
};

/**
 * Factory function which builds a panel for a generic model feature (e.g. 'attachments')
 */
export type ModelFeaturePanelFactory = (
  props: Readonly<ModelFeaturePanelProps>
) => PanelType | Promise<PanelType>;

/**
 * Type used to specify a group of panels
 */
export type PanelGroupType = {
  id: string;
  label: string;
  panelIDs?: string[];
  panels?: PanelType[];
};
