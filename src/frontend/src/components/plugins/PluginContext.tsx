import {
  MantineColorScheme,
  MantineTheme,
  useMantineColorScheme,
  useMantineTheme
} from '@mantine/core';
import { AxiosInstance } from 'axios';
import { useMemo } from 'react';
import { NavigateFunction, useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { useLocalState } from '../../states/LocalState';
import {
  SettingsStateProps,
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsState';
import { UserStateProps, useUserState } from '../../states/UserState';

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
 */
export type InvenTreeContext = {
  api: AxiosInstance;
  user: UserStateProps;
  userSettings: SettingsStateProps;
  globalSettings: SettingsStateProps;
  host: string;
  navigate: NavigateFunction;
  theme: MantineTheme;
  colorScheme: MantineColorScheme;
};

export const useInvenTreeContext = () => {
  const host = useLocalState((s) => s.host);
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
      api: api,
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
    navigate,
    globalSettings,
    userSettings,
    theme,
    colorScheme
  ]);

  return contextData;
};
