import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { api } from '../App';
import type { DashboardWidgetProps } from '../components/dashboard/DashboardWidget';
import DashboardWidgetLibrary from '../components/dashboard/DashboardWidgetLibrary';
import { useInvenTreeContext } from '../components/plugins/PluginContext';
import {
  type PluginUIFeature,
  PluginUIFeatureType
} from '../components/plugins/PluginUIFeature';
import RemoteComponent from '../components/plugins/RemoteComponent';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { identifierString } from '../functions/conversion';
import { apiUrl } from '../states/ApiState';
import { useGlobalSettingsState } from '../states/SettingsState';
import { useUserState } from '../states/UserState';

interface DashboardLibraryProps {
  items: DashboardWidgetProps[];
  loaded: boolean;
}

/**
 * Custom hook to load available dashboard items.
 *
 * - Loads from library of "builtin" dashboard items
 * - Loads plugin-defined dashboard items (via the API)
 */
export function useDashboardItems(): DashboardLibraryProps {
  const user = useUserState();
  const globalSettings = useGlobalSettingsState();

  const pluginsEnabled: boolean = useMemo(
    () => globalSettings.isSet('ENABLE_PLUGINS_INTERFACE'),
    [globalSettings]
  );

  const builtin = DashboardWidgetLibrary();

  const pluginQuery = useQuery({
    enabled: pluginsEnabled,
    queryKey: ['plugin-dashboard-items', user],
    refetchOnMount: true,
    queryFn: async () => {
      if (!pluginsEnabled) {
        return Promise.resolve([]);
      }

      const url = apiUrl(ApiEndpoints.plugin_ui_features_list, undefined, {
        feature_type: PluginUIFeatureType.dashboard
      });

      return api
        .get(url)
        .then((response: any) => response.data)
        .catch((_error: any) => {
          console.error('ERR: Failed to fetch plugin dashboard items');
          return [];
        });
    }
  });

  // Cache the context data which is delivered to the plugins
  const inventreeContext = useInvenTreeContext();

  const pluginDashboardItems: DashboardWidgetProps[] = useMemo(() => {
    return (
      pluginQuery?.data?.map((item: PluginUIFeature) => {
        const pluginContext = {
          ...inventreeContext,
          context: item.context
        };

        return {
          label: identifierString(`p-${item.plugin_name}-${item.key}`),
          title: item.title,
          description: item.description,
          minWidth: item.options?.width ?? 2,
          minHeight: item.options?.height ?? 1,
          render: () => {
            return (
              <RemoteComponent
                source={item.source}
                defaultFunctionName='renderDashboardItem'
                context={pluginContext}
              />
            );
          }
        };
      }) ?? []
    );
  }, [pluginQuery, inventreeContext]);

  const items: DashboardWidgetProps[] = useMemo(() => {
    const widgets = [...builtin, ...pluginDashboardItems];

    return widgets.filter((item) => item.enabled ?? true);
  }, [builtin, pluginDashboardItems]);

  const loaded: boolean = useMemo(() => {
    if (pluginsEnabled) {
      return (
        !pluginQuery.isFetching &&
        !pluginQuery.isLoading &&
        pluginQuery.isFetched &&
        pluginQuery.isSuccess
      );
    } else {
      return true;
    }
  }, [pluginsEnabled, pluginQuery]);

  return {
    items: items,
    loaded: loaded
  };
}
