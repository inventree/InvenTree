import {
  type MantineColorScheme,
  type MantineTheme,
  useMantineColorScheme,
  useMantineTheme
} from '@mantine/core';
import type { AxiosInstance } from 'axios';
import { useMemo } from 'react';
import { type NavigateFunction, useNavigate } from 'react-router-dom';

import type { QueryClient } from '@tanstack/react-query';
import { api, queryClient } from '../../App';
import { useLocalState } from '../../states/LocalState';
import {
  type SettingsStateProps,
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsState';
import { type UserStateProps, useUserState } from '../../states/UserState';

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
export type InvenTreeContext = {
  api: AxiosInstance;
  queryClient: QueryClient;
  user: UserStateProps;
  userSettings: SettingsStateProps;
  globalSettings: SettingsStateProps;
  host: string;
  locale: string;
  navigate: NavigateFunction;
  theme: MantineTheme;
  colorScheme: MantineColorScheme;
  context?: any;
};

export const useInvenTreeContext = () => {
  const [locale, host] = useLocalState((s) => [s.language, s.host]);
  const navigate = useNavigate();
  const user = useUserState();
  const { colorScheme } = useMantineColorScheme();
  const theme = useMantineTheme();
  const globalSettings = useGlobalSettingsState();
  const userSettings = useUserSettingsState();

  const contextData = useMemo<InvenTreeContext>(() => {
    return {
      user: user,
      host: host,
      locale: locale,
      api: api,
      queryClient: queryClient,
      navigate: navigate,
      globalSettings: globalSettings,
      userSettings: userSettings,
      theme: theme,
      colorScheme: colorScheme
    };
  }, [
    user,
    host,
    api,
    locale,
    queryClient,
    navigate,
    globalSettings,
    userSettings,
    theme,
    colorScheme
  ]);

  return contextData;
};
