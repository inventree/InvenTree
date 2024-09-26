import { MantineColorScheme, MantineTheme } from '@mantine/core';
import { AxiosInstance } from 'axios';
import { NavigateFunction } from 'react-router-dom';

import { ModelType } from '../../enums/ModelType';
import { SettingsStateProps } from '../../states/SettingsState';
import { UserStateProps } from '../../states/UserState';

/*
 * A set of properties which are passed to a plugin,
 * for rendering an element in the user interface.
 *
 * @param model - The model type for the plugin (e.g. 'part' / 'purchaseorder')
 * @param id - The ID (primary key) of the model instance for the plugin
 * @param instance - The model instance data (if available)
 * @param context - Optional custom context data for rendering
 * @param api - The Axios API instance (see ../states/ApiState.tsx)
 * @param user - The current user instance (see ../states/UserState.tsx)
 * @param userSettings - The current user settings (see ../states/SettingsState.tsx)
 * @param globalSettings - The global settings (see ../states/SettingsState.tsx)
 * @param navigate - The navigation function (see react-router-dom)
 * @param theme - The current Mantine theme
 * @param colorScheme - The current Mantine color scheme (e.g. 'light' / 'dark')
 */
export type PluginContext = {
  model?: ModelType | string;
  id?: string | number | null;
  instance?: any;
  context?: any;
  api: AxiosInstance;
  user: UserStateProps;
  userSettings: SettingsStateProps;
  globalSettings: SettingsStateProps;
  host: string;
  navigate: NavigateFunction;
  theme: MantineTheme;
  colorScheme: MantineColorScheme;
};
