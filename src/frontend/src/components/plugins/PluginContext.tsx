import { ModelInformationDict } from '@lib/enums/ModelInformation';
import {
  INVENTREE_MANTINE_VERSION,
  INVENTREE_PLUGIN_VERSION,
  INVENTREE_REACT_VERSION,
  type InvenTreePluginContext
} from '@lib/types/Plugins';
import type { InvenTreeTableRenderProps } from '@lib/types/Tables';
import { i18n } from '@lingui/core';
import { useMantineColorScheme, useMantineTheme } from '@mantine/core';
import { useContextMenu } from 'mantine-contextmenu';
import { Suspense, lazy, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useShallow } from 'zustand/react/shallow';
import { api, queryClient } from '../../App';
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
import { useLocalState } from '../../states/LocalState';
import { usePluginState } from '../../states/PluginState';
import {
  closeGlobalPreview,
  getGlobalPreviewState,
  openGlobalPreview
} from '../../states/PreviewDrawerState';
import { useServerApiState } from '../../states/ServerApiState';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import { EditApiForm } from '../forms/ApiForm';
import { Thumbnail } from '../images/Thumbnail';
import {
  RenderInlineModel,
  RenderInstance,
  RenderRemoteInstance
} from '../render/Instance';

// Lazy loaded: useInvenTreeContext is used by the always-mounted nav Layout
// to build the context handed to plugins, but tables.renderTable is only
// ever actually called by a plugin that chooses to render a table - which
// is rare. Loading InvenTreeTable's (sizeable) module here unconditionally
// would mean every page load pays for it regardless of whether any plugin
// uses it.
const InvenTreeTableInternal = lazy(() =>
  import('../tables/InvenTreeTable').then((m) => ({
    default: m.InvenTreeTableInternal
  }))
);

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
      preview: {
        open: (modelType, id?, instance?, onClose?) =>
          openGlobalPreview(modelType, id, instance, undefined, onClose),
        close: () => closeGlobalPreview(),
        isOpen: () => getGlobalPreviewState().isOpen
      },
      tables: {
        renderTable: (props: InvenTreeTableRenderProps<any>) => (
          <Suspense fallback={null}>
            <InvenTreeTableInternal
              {...props}
              showContextMenu={showContextMenu}
            />
          </Suspense>
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
