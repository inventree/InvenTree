import { useQuery } from '@tanstack/react-query';
import { truncateSync } from 'fs';
import { useMemo } from 'react';

import { api } from '../App';
import { DashboardWidgetProps } from '../components/dashboard/DashboardWidget';
import DashboardWidgetLibrary from '../components/dashboard/DashboardWidgetLibrary';
import { useInvenTreeContext } from '../components/plugins/PluginContext';
import RemoteComponent from '../components/plugins/RemoteComponent';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { identifierString } from '../functions/conversion';
import { apiUrl } from '../states/ApiState';
import { useGlobalSettingsState } from '../states/SettingsState';
import { useUserState } from '../states/UserState';

// Define the interface for a plugin-defined dashboard item
interface PluginDashboardItem {
  plugin: string;
  label: string;
  title: string;
  description: string;
  width?: number;
  height?: number;
  source: string;
}

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

      console.log('fetching plugin dashboard items...');

      return api
        .get(apiUrl(ApiEndpoints.plugin_dashboard_list), {})
        .then((response: any) => response.data)
        .catch((error: any) => {
          console.error('Failed to fetch plugin dashboard items:', error);
          return [];
        });
    }
  });

  // Cache the context data which is delivered to the plugins
  const inventreeContext = useInvenTreeContext();

  const pluginDashboardItems: DashboardWidgetProps[] = useMemo(() => {
    return (
      pluginQuery?.data?.map((item: PluginDashboardItem) => {
        return {
          label: identifierString(`p-${item.plugin}-${item.label}`),
          title: item.title,
          description: item.description,
          minWidth: item.width,
          minHeight: item.height,
          render: () => {
            return (
              <RemoteComponent
                source={item.source}
                funcName="renderDashboardItem"
                context={inventreeContext}
              />
            );
          }
        };
      }) ?? []
    );
  }, [pluginQuery]);

  const items: DashboardWidgetProps[] = useMemo(() => {
    return [...builtin, ...pluginDashboardItems];
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
