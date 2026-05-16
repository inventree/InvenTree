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
import type { InvenTreeTableRenderProps } from '@lib/types/Tables';
import { i18n } from '@lingui/core';
import { useContextMenu } from 'mantine-contextmenu';
import { defaultLocale } from '../../contexts/LanguageContext';
import {
  useAddStockItem,
  useAssignStockItem,
  useChangeStockStatus,
  useCountStockItem,
  useDeleteStockItem,
  useMergeStockItem,
  useRemoveStockItem,
  useReturnStockItem,
  useTransferStockItem
} from '../../forms/StockForms';
import {
  useBulkEditApiFormModal,
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import {
  type ImporterOpenOptions,
  closeGlobalImporter,
  getGlobalImporterState,
  openGlobalImporter
} from '../../states/ImporterState';
import { usePluginState } from '../../states/PluginState';
import { useServerApiState } from '../../states/ServerApiState';
import { InvenTreeTableInternal } from '../../tables/InvenTreeTable';
import { EditApiForm } from '../forms/ApiForm';
import { Thumbnail } from '../images/Thumbnail';
import { RenderInstance, RenderRemoteInstance } from '../render/Instance';
import { RenderInlineModel } from '../render/Instance';

export const useInvenTreeContext = () => {
  const [locale, host] = useLocalState(useShallow((s) => [s.language, s.host]));
  const [server] = useServerApiState(useShallow((s) => [s.server]));
  const [setRenderer] = usePluginState(useShallow((s) => [s.setRenderer]));
  const navigate = useNavigate();
  const user = useUserState();
  const { colorScheme } = useMantineColorScheme();
  const theme = useMantineTheme();
  const globalSettings = useGlobalSettingsState();
  const userSettings = useUserSettingsState();
  const { showContextMenu } = useContextMenu();

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
      i18n: i18n,
      locale: locale || server.default_locale || defaultLocale,
      api: api,
      queryClient: queryClient,
      navigate: navigate,
      globalSettings: globalSettings,
      userSettings: userSettings,
      modelInformation: ModelInformationDict,
      useInstance: useInstance,
      renderInstance: RenderInstance,
      renderRemoteInstance: RenderRemoteInstance,
      renderInlineModel: RenderInlineModel,
      thumbnail: Thumbnail,
      theme: theme,
      colorScheme: colorScheme,
      importer: {
        open: (sessionId: number, options?: ImporterOpenOptions) =>
          openGlobalImporter(sessionId, options),
        close: () => closeGlobalImporter(),
        isOpen: () => getGlobalImporterState().isOpen,
        sessionId: () => getGlobalImporterState().sessionId
      },
      tables: {
        renderTable: (props: InvenTreeTableRenderProps<any>) => (
          <InvenTreeTableInternal
            {...props}
            showContextMenu={showContextMenu}
          />
        )
      },
      forms: {
        bulkEdit: useBulkEditApiFormModal,
        create: useCreateApiFormModal,
        delete: useDeleteApiFormModal,
        edit: useEditApiFormModal,
        editApiForm: EditApiForm,
        stockActions: {
          addStock: useAddStockItem,
          assignStock: useAssignStockItem,
          changeStatus: useChangeStockStatus,
          countStock: useCountStockItem,
          deleteStock: useDeleteStockItem,
          mergeStock: useMergeStockItem,
          removeStock: useRemoveStockItem,
          transferStock: useTransferStockItem,
          returnStock: useReturnStockItem
        }
      },
      stateFnc: {
        setRenderer: setRenderer
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
