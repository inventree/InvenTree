import type { MantineColorScheme, MantineTheme } from '@mantine/core';
import type { QueryClient } from '@tanstack/react-query';
import type { AxiosInstance } from 'axios';
import type { NavigateFunction } from 'react-router-dom';
import type { ModelType } from '../enums/ModelType';
import type { ApiFormModalProps, BulkEditApiFormModalProps } from './Forms';
import type { UseModalReturn } from './Modals';
import type { SettingsStateProps } from './Settings';
import type { UserStateProps } from './User';

export interface PluginProps {
  name: string;
  slug: string;
  version: null | string;
}

export type InvenTreeFormsContext = {
  bulkEdit: (props: BulkEditApiFormModalProps) => UseModalReturn;
  create: (props: ApiFormModalProps) => UseModalReturn;
  delete: (props: ApiFormModalProps) => UseModalReturn;
  edit: (props: ApiFormModalProps) => UseModalReturn;
};

/**
 * A set of properties which are passed to a plugin,
 * for rendering an element in the user interface.
 *
 * @param api - The Axios API instance (see ../states/ApiState.tsx)
 * @param user - The current user instance (see ../states/UserState.tsx)
 * @param userSettings - The current user settings (see ../states/SettingsState.tsx)
 * @param globalSettings - The global settings (see ../states/SettingsState.tsx)
 * @param navigate - The navigation function (see react-router-dom)
 * @param theme - The current Mantine theme
 * @param colorScheme - The current Mantine color scheme (e.g. 'light' / 'dark')
 * @param host - The current host URL
 * @param locale - The current locale string (e.g. 'en' / 'de')
 * @param pluginContext - Any additional context data which may be passed to the plugin
 * @param model - The model type associated with the rendered component (if applicable)
 * @param id - The ID (primary key) of the model instance for the plugin (if applicable)
 * @param instance - The model instance data (if available)
 */
export type InvenTreePluginContext = {
  api: AxiosInstance;
  queryClient: QueryClient;
  user: UserStateProps;
  userSettings: SettingsStateProps;
  globalSettings: SettingsStateProps;
  host: string;
  locale: string;
  navigate: NavigateFunction;
  theme: MantineTheme;
  forms: InvenTreeFormsContext;
  colorScheme: MantineColorScheme;
  pluginContext?: any;
  model?: ModelType | string;
  id?: string | number | null;
  instance?: any;
};
