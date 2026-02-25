import { t } from '@lingui/core/macro';
import { Container, Flex, Space } from '@mantine/core';
import {
  Spotlight,
  type SpotlightActionData,
  createSpotlight
} from '@mantine/spotlight';
import { IconSearch } from '@tabler/icons-react';
import { type JSX, useEffect, useMemo, useState } from 'react';
import { Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom';

import { identifierString } from '@lib/functions/Conversion';
import { ApiEndpoints, apiUrl } from '@lib/index';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../App';
import { getActions } from '../../defaults/actions';
import * as classes from '../../main.css';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import { Boundary } from '../Boundary';
import { ApiIcon } from '../items/ApiIcon';
import { useInvenTreeContext } from '../plugins/PluginContext';
import { callExternalPluginFunction } from '../plugins/PluginSource';
import {
  type PluginUIFeature,
  PluginUIFeatureType
} from '../plugins/PluginUIFeature';
import { Footer } from './Footer';
import { Header } from './Header';

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

export default function LayoutComponent() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = useUserState();
  const userSettings = useUserSettingsState();
  const globalSettings = useGlobalSettingsState();

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
      <Flex direction='column' mih='100vh'>
        <Header />
        <Container className={classes.layoutContent} size='100%'>
          <Boundary label={'layout'}>
            <Outlet />
          </Boundary>
          {/* </ErrorBoundary> */}
        </Container>
        <Space h='xl' />
        <Footer />
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
            shortcut={['mod + K']}
            nothingFound={t`Nothing found...`}
          />
        )}
      </Flex>
    </ProtectedRoute>
  );
}
