import { type UseQueryResult, useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type { InvenTreePluginContext } from '@lib/types/Plugins';
import { api } from '../App';
import { ApiIcon } from '../components/items/ApiIcon';
import type { PanelType } from '../components/panels/Panel';
import { useInvenTreeContext } from '../components/plugins/PluginContext';
import PluginPanelContent from '../components/plugins/PluginPanel';
import {
  type PluginUIFeature,
  PluginUIFeatureType
} from '../components/plugins/PluginUIFeature';
import { useGlobalSettingsState } from '../states/SettingsState';

/**
 * Type definition for a plugin panel which extends the standard PanelType
 * @param pluginName - The name of the plugin which provides this panel
 */
export type PluginPanelType = PanelType & {
  pluginName: string;
  isLoading: boolean;
};

export type PluginPanelSet = {
  panels: PluginPanelType[];
  query: UseQueryResult;
  isLoading: boolean;
};

export function usePluginPanels({
  instance,
  reloadFunc,
  model,
  id
}: {
  instance?: any;
  reloadFunc?: () => void;
  model?: ModelType | string;
  id?: string | number | null;
}): PluginPanelSet {
  const globalSettings = useGlobalSettingsState();

  const pluginPanelsEnabled: boolean = useMemo(
    () => globalSettings.isSet('ENABLE_PLUGINS_INTERFACE'),
    [globalSettings]
  );

  // API query to fetch initial information on available plugin panels
  const pluginQuery = useQuery({
    enabled: pluginPanelsEnabled && !!model && id !== undefined,
    queryKey: ['custom-plugin-panels', model, id],
    throwOnError: (error: any) => {
      console.error('ERR: Failed to fetch plugin panels');
      return false;
    },
    queryFn: async () => {
      if (!pluginPanelsEnabled || !model) {
        return Promise.resolve([]);
      }

      const url = apiUrl(ApiEndpoints.plugin_ui_features_list, undefined, {
        feature_type: PluginUIFeatureType.panel
      });

      return api
        .get(url, {
          params: {
            target_model: model,
            target_id: id
          }
        })
        .then((response: any) => response.data);
    }
  });

  // Cache the context data which is delivered to the plugins
  const inventreeContext = useInvenTreeContext();

  const contextData: InvenTreePluginContext =
    useMemo<InvenTreePluginContext>(() => {
      return {
        ...inventreeContext,
        id: id,
        model: model,
        instance: instance,
        reloadInstance: reloadFunc
      };
    }, [model, id, instance, inventreeContext]);

  const pluginPanels: PluginPanelType[] = useMemo(() => {
    return (
      pluginQuery?.data?.map((props: PluginUIFeature) => {
        const iconName: string = props?.icon || 'ti:plug:outline';

        const ctx: InvenTreePluginContext = {
          ...contextData,
          context: props.context
        };

        return {
          name: props.key,
          pluginName: props.plugin_name,
          label: props.title,
          icon: <ApiIcon name={iconName} />,
          content: (
            <PluginPanelContent pluginFeature={props} pluginContext={ctx} />
          )
        };
      }) ?? []
    );
  }, [pluginQuery.data, contextData]);

  const panelSet: PluginPanelSet = useMemo(() => {
    return {
      panels: pluginPanels,
      isLoading: pluginQuery.isLoading || pluginQuery.isFetching,
      query: pluginQuery
    };
  }, [pluginPanels, pluginQuery]);

  return panelSet;
}
