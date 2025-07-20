import { useMantineColorScheme, useMantineTheme } from '@mantine/core';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useShallow } from 'zustand/react/shallow';
import { api, queryClient } from '../../App';
import { useLocalState } from '../../states/LocalState';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';

import { ModelInformationDict } from '@lib/enums/ModelInformation';
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
import { RenderInstance } from '../render/Instance';

export const useInvenTreeContext = () => {
  const [locale, host] = useLocalState(useShallow((s) => [s.language, s.host]));
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
      modelInformation: ModelInformationDict,
      renderInstance: RenderInstance,
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
