import { useMantineColorScheme, useMantineTheme } from '@mantine/core';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { api, queryClient } from '../../App';
import { useLocalState } from '../../states/LocalState';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';

import {
  INVENTREE_MANTINE_VERSION,
  INVENTREE_PLUGIN_VERSION,
  INVENTREE_REACT_VERSION,
  type InvenTreePluginContext
} from '@lib/types/Plugins';
import {
  useBulkEditApiFormModal,
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';

export const useInvenTreeContext = () => {
  const [locale, host] = useLocalState((s) => [s.language, s.host]);
  const navigate = useNavigate();
  const user = useUserState();
  const { colorScheme } = useMantineColorScheme();
  const theme = useMantineTheme();
  const globalSettings = useGlobalSettingsState();
  const userSettings = useUserSettingsState();

  const contextData = useMemo<InvenTreePluginContext>(() => {
    return {
      version: {
        inventree: INVENTREE_PLUGIN_VERSION,
        react: INVENTREE_REACT_VERSION,
        reactDom: INVENTREE_REACT_VERSION,
        mantine: INVENTREE_MANTINE_VERSION
      },
      user: user,
      host: host,
      locale: locale,
      api: api,
      queryClient: queryClient,
      navigate: navigate,
      globalSettings: globalSettings,
      userSettings: userSettings,
      theme: theme,
      colorScheme: colorScheme,
      forms: {
        bulkEdit: useBulkEditApiFormModal,
        create: useCreateApiFormModal,
        delete: useDeleteApiFormModal,
        edit: useEditApiFormModal
      }
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
