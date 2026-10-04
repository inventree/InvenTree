import { t } from '@lingui/core/macro';
import { Box, Container, Flex, useMantineColorScheme } from '@mantine/core';
import {
  Spotlight,
  type SpotlightActionData,
  createSpotlight
} from '@mantine/spotlight';
import { IconSearch } from '@tabler/icons-react';
import { type JSX, useEffect, useMemo, useState } from 'react';
import { Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom';

import { Boundary } from '@lib/components/Boundary';
import { identifierString } from '@lib/functions/Conversion';
import { ApiEndpoints, apiUrl } from '@lib/index';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../App';
import { getActions } from '../../defaults/actions';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import GlobalImporterDrawer from '../importer/GlobalImporterDrawer';
import { ApiIcon } from '../items/ApiIcon';
import { useInvenTreeContext } from '../plugins/PluginContext';
import { callExternalPluginFunction } from '../plugins/PluginSource';
import {
  type PluginUIFeature,
  PluginUIFeatureType
} from '../plugins/PluginUIFeature';
import GlobalPreviewDrawer from '../previews/GlobalPreviewDrawer';
import { AppSidebar } from './AppSidebar';
import { TopBar } from './TopBar';

export const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const location = useLocation();
  const { isLoggedIn } = useUserState();

  if (!isLoggedIn()) {
    return (
      <Navigate
        to='/logged-in'
        state={{
          redirectUrl: location.pathname,
          queryParams: location.search,
          anchor: location.hash
        }}
      />
    );
  }

  return children;
};

export const [firstStore, firstSpotlight] = createSpotlight();

export const searchShortcutKey = 'mod+K';

export default function LayoutComponent() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = useUserState();
  const userSettings = useUserSettingsState();
  const globalSettings = useGlobalSettingsState();
  const { colorScheme } = useMantineColorScheme();
  const isDark = colorScheme === 'dark';

  const pluginsEnabled: boolean = useMemo(
    () => globalSettings.isSet('ENABLE_PLUGINS_INTERFACE'),
    [globalSettings]
  );

  const inventreeContext = useInvenTreeContext();

  const defaultActions = getActions(navigate);
  const [actions, setActions] = useState(defaultActions);

  const pluginActionsQuery = useQuery({
    enabled: pluginsEnabled,
    queryKey: ['plugin-actions', pluginsEnabled, user],
    refetchOnMount: true,
    queryFn: async () => {
      if (!pluginsEnabled) {
        return Promise.resolve([]);
      }

      const url = apiUrl(ApiEndpoints.plugin_ui_features_list, undefined, {
        feature_type: PluginUIFeatureType.spotlight_action
      });

      return api.get(url).then((response: any) => response.data);
    }
  });

  const pluginActions: SpotlightActionData[] = useMemo(() => {
    return (
      pluginActionsQuery?.data?.map((item: PluginUIFeature) => {
        const pluginContext = {
          ...inventreeContext,
          context: item.context
        };

        return {
          id: identifierString(`a-${item.plugin_name}-${item.key}`),
          label: item.title,
          description: item.description,
          leftSection: item.icon && <ApiIcon name={item.icon} />,
          onClick: () => {
            callExternalPluginFunction(
              item.source,
              'executeAction',
              pluginContext
            );
          }
        };
      }) ?? []
    );
  }, [pluginActionsQuery?.data, inventreeContext]);

  useEffect(() => {
    setActions([...defaultActions, ...pluginActions]);
  }, [defaultActions.length, pluginActions.length, location]);

  return (
    <ProtectedRoute>
      <>
        {/* ── Root: sidebar on left, content on right ── */}
        <Box
          style={{
            display: 'flex',
            flexDirection: 'row',
            minHeight: '100vh',
            width: '100%'
          }}
        >
          {/* Left Sidebar */}
          <AppSidebar />

          {/* Right: topbar + page content */}
          <Flex
            direction='column'
            style={{ flex: 1, minWidth: 0, overflow: 'hidden' }}
          >
            {/* Top bar with search/icons/user */}
            <TopBar />

            {/* Page content */}
            <Box
              style={{
                flex: 1,
                overflow: 'auto',
                padding: '20px 24px',
                background: isDark
                  ? '#090d16'
                  : 'linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 50%, #eaeff5 100%)',
                minHeight: 0
              }}
            >
              <Boundary label={'layout'}>
                <Outlet />
              </Boundary>
            </Box>
          </Flex>
        </Box>

        {/* Spotlight search */}
        {userSettings.isSet('SHOW_SPOTLIGHT') && (
          <Spotlight
            actions={actions}
            store={firstStore}
            highlightQuery
            scrollable
            searchProps={{
              leftSection: <IconSearch size='1.2rem' />,
              placeholder: t`Search...`
            }}
            shortcut={[searchShortcutKey]}
            nothingFound={t`Nothing found...`}
          />
        )}

        <GlobalImporterDrawer />
        <GlobalPreviewDrawer />
      </>
    </ProtectedRoute>
  );
}
