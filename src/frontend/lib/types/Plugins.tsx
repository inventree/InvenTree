import type { MantineColorScheme, MantineTheme } from '@mantine/core';
import type { QueryClient } from '@tanstack/react-query';
import type { AxiosInstance } from 'axios';
import type { NavigateFunction } from 'react-router-dom';
import type { SettingsStateProps } from '../../src/states/SettingsState';
import type { UserStateProps } from '../../src/states/UserState';
import type { ApiFormModalProps, BulkEditApiFormModalProps } from './Forms';
import type { UseModalReturn } from './Modals';

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
 * @param context - Any additional context data which may be passed to the plugin
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
  context?: any;
};
